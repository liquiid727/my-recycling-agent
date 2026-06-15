/*
 * CN: 规划流程 hook，管理提交状态、阶段事件、错误、跳转和最终结果。
 * EN: Planner flow hook that manages submission state, stage events, errors, navigation, and final results.
 */

import { FormEvent, useState } from "react";

import {
  ChatTurnMessage,
  createChatTurn,
  createRidePlan,
  createRidePlanStream,
  InputMode,
  PlannerRequest,
  PlannerStageUpdate,
  RideIntent,
  PlanningMode,
  PlanningScene,
  RidePlanResponse,
  StructuredConstraints
} from "./api";
import { loadUserProfile } from "../settings/store";

type PlannerState = {
  messages: PlannerMessage[];
  query: string;
  intent: RideIntent;
  planningMode: PlanningMode;
  planningScene: PlanningScene;
  inputMode: InputMode;
  targetDate: string;
  structuredConstraints: StructuredConstraints;
  slotState: Record<string, unknown>;
  quickReplies: string[];
  clarificationPrompt: string | null;
  loading: boolean;
  loadingLabel: string | null;
  error: string | null;
  result: RidePlanResponse | null;
  stageUpdates: PlannerStageUpdate[];
};

export type PlannerMessage = {
  id: string;
  role: "assistant" | "user";
  content: string;
};

const INITIAL_QUERY = "我今天晚上想出去骑行一下";
const INITIAL_RIDE_PLAN_QUERY = "帮我安排一次轻松骑行";
const INITIAL_NEARBY_QUERY = "周末想出去骑车，附近有什么推荐线路么";
const INITIAL_CITY_MESSAGE = "嗨，我是 AAA骑车帮帮。你可以直接说“我今天晚上想出去骑行一下”，我会像朋友一样帮你判断今晚适不适合骑。";
const INITIAL_RIDE_PLAN_MESSAGE = "嗨，我是 AAA骑车帮帮。你可以直接说出发点、时长和风格，我会先给结论，再给你稳妥路线。";
const INITIAL_WEEKEND_MESSAGE = "嗨，我是 AAA骑车帮帮。周末想出去骑车也可以直接说，我会帮你看目的地、天数、住宿和返程。";
const DEFAULT_QUICK_REPLIES: Record<RideIntent, string[]> = {
  ride_today: ["今天适合骑吗", "今晚轻松骑", "现在出发", "不要爬坡"],
  ride_plan: ["从滨江出发", "骑 2 小时", "不要爬坡", "轻松点"],
  weekend_recommendation: ["周末两天", "一天往返", "千岛湖", "公共交通返程"],
};

type UsePlannerFlowOptions = {
  onSuccess?: (result: RidePlanResponse) => void;
};

export function usePlannerFlow(options?: UsePlannerFlowOptions) {
  const [state, setState] = useState<PlannerState>({
    messages: [buildMessage("assistant", INITIAL_CITY_MESSAGE)],
    query: INITIAL_QUERY,
    intent: "ride_today",
    planningMode: "route",
    planningScene: "city_ride",
    inputMode: "natural",
    targetDate: "2026-05-30",
    structuredConstraints: {
      departure_time: "07:00",
      origin_region: "滨江",
      start_point: "闻涛路滨江段",
      available_hours: 3,
      target_distance_km: 42,
      fitness_level: "medium",
      ride_style: "scenic_relaxed",
      slope_tolerance: "avoid",
      priority: "风景",
      duration_bucket: "evening",
      destination_preferences: ["江边", "咖啡"],
      return_preference: "ride_back"
    },
    slotState: {},
    quickReplies: DEFAULT_QUICK_REPLIES.ride_today,
    clarificationPrompt: null,
    loading: false,
    loadingLabel: null,
    error: null,
    result: null,
    stageUpdates: []
  });

  async function submit(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const submittedText = state.query.trim();
    if (state.inputMode === "natural" && !submittedText) {
      setState((current) => ({ ...current, error: "请输入你的骑行需求" }));
      return;
    }

    setState((current) => ({
      ...current,
      messages: [
        ...current.messages,
        buildMessage("user", current.inputMode === "natural" ? submittedText : buildStructuredUserMessage(current))
      ],
      loading: true,
      loadingLabel: state.inputMode === "natural" ? "AAA骑车帮帮正在理解你的想法" : getLoadingLabel(state.intent),
      error: null,
      result: null,
      clarificationPrompt: null,
      stageUpdates: []
    }));

    try {
      const userProfile = loadUserProfile();
      if (state.inputMode === "natural") {
        const chatMessages: ChatTurnMessage[] = [
          ...state.messages.map((message) => ({ role: message.role, content: message.content })),
          { role: "user", content: submittedText }
        ];
        const chatTurn = await createChatTurn(
          {
            messages: chatMessages,
            intent: state.intent,
            planning_scene: state.planningScene,
            target_date: state.targetDate,
            slot_state: state.slotState
          },
          userProfile
        );

        if (!chatTurn.ready_to_plan || !chatTurn.planner_request) {
          setState((current) => ({
            ...current,
            ...resolveNextIntentState(chatTurn.intent ?? current.intent),
            slotState: chatTurn.slot_state,
            quickReplies:
              chatTurn.ui_hints?.quick_replies?.length
                ? chatTurn.ui_hints.quick_replies
                : DEFAULT_QUICK_REPLIES[chatTurn.intent ?? current.intent] ?? DEFAULT_QUICK_REPLIES.ride_today,
            clarificationPrompt: null,
            query: "",
            messages: [
              ...current.messages,
              buildMessage("assistant", chatTurn.assistant_message)
            ],
            loading: false,
            loadingLabel: null
          }));
          return;
        }
        setState((current) => ({
          ...current,
          ...resolveNextIntentState(chatTurn.intent ?? current.intent),
          slotState: chatTurn.slot_state,
          quickReplies:
            chatTurn.ui_hints?.quick_replies?.length
              ? chatTurn.ui_hints.quick_replies
              : DEFAULT_QUICK_REPLIES[chatTurn.intent ?? current.intent] ?? DEFAULT_QUICK_REPLIES.ride_today,
          messages: [...current.messages, buildMessage("assistant", chatTurn.assistant_message)],
          loadingLabel: chatTurn.ui_hints?.planning_status_label ?? "我在看天气和路线难度"
        }));
        const result = await createRidePlanStream(chatTurn.planner_request, userProfile, {
          onStage: (stage) => {
            setState((current) => ({
              ...current,
              stageUpdates: [...current.stageUpdates, stage]
            }));
          }
        }).catch(async () => createRidePlan(chatTurn.planner_request as PlannerRequest, userProfile));
        setState((current) => ({
          ...current,
          loading: false,
          loadingLabel: null,
          result,
          query: "",
          messages: [...current.messages, buildMessage("assistant", result.decision_summary?.decision_title ?? "路线看好了，我把结论和可选路线放在下面。")]
        }));
        options?.onSuccess?.(result);
        return;
      }

      const request = buildPlannerRequest(state);
      setState((current) => ({ ...current, loadingLabel: getLoadingLabel(state.intent) }));
      const result = await createRidePlanStream(request, userProfile, {
        onStage: (stage) => {
          setState((current) => ({
            ...current,
            stageUpdates: [...current.stageUpdates, stage]
          }));
        }
      }).catch(async () => createRidePlan(request, userProfile));
      setState((current) => ({
        ...current,
        loading: false,
        loadingLabel: null,
        result,
        query: "",
        messages: [
          ...current.messages,
          buildMessage("assistant", result.decision_summary?.decision_title ?? "方案已生成，我把结论和详细路线放在下面。")
        ]
      }));
      options?.onSuccess?.(result);
    } catch {
      setState((current) => ({
        ...current,
        loading: false,
        loadingLabel: null,
        error: "规划服务暂时不可用，请稍后再试。",
        messages: [...current.messages, buildMessage("assistant", "规划服务暂时不可用，请稍后再试。")],
        stageUpdates: []
      }));
    }
  }

  function setQuery(query: string) {
    setState((current) => ({ ...current, query }));
  }

  function setInputMode(inputMode: InputMode) {
    setState((current) => ({ ...current, inputMode, error: null, clarificationPrompt: null }));
  }

  function setIntent(intent: RideIntent) {
    const { planningMode, planningScene } = getExecutionContext(intent);
    setState((current) => ({
      ...current,
      intent,
      planningMode,
      planningScene,
      query: getInitialQuery(intent),
      messages: [buildMessage("assistant", getInitialAssistantMessage(intent))],
      slotState: {},
      quickReplies: DEFAULT_QUICK_REPLIES[intent],
      inputMode: "natural",
      structuredConstraints: {
        ...current.structuredConstraints,
        available_hours: intent === "weekend_recommendation" ? undefined : current.structuredConstraints.available_hours,
        duration_bucket: intent === "weekend_recommendation" ? "two_day" : "evening",
        destination_preferences: intent === "weekend_recommendation" ? ["千岛湖"] : current.structuredConstraints.destination_preferences,
        return_preference: intent === "weekend_recommendation" ? "public_transport" : current.structuredConstraints.return_preference,
        overnight_preference: intent === "weekend_recommendation" ? "optional" : undefined,
      },
      error: null,
      clarificationPrompt: null
    }));
  }

  function setTargetDate(targetDate: string) {
    setState((current) => ({ ...current, targetDate }));
  }

  function setStructuredField(field: keyof StructuredConstraints, value: string | string[]) {
    setState((current) => ({
      ...current,
      structuredConstraints: {
        ...current.structuredConstraints,
        [field]: field === "available_hours" || field === "target_distance_km" ? parseNumber(String(value)) : value
      }
    }));
  }

  function detectOriginLocation() {
    if (!navigator.geolocation) {
      setState((current) => ({ ...current, error: "当前浏览器不支持定位，请手动输入出发点。" }));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setState((current) => ({
          ...current,
          error: null,
          structuredConstraints: {
            ...current.structuredConstraints,
            start_point: current.structuredConstraints.start_point || "当前位置",
            origin_location: {
              name: current.structuredConstraints.start_point || "当前位置",
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              source: "browser"
            }
          }
        }));
      },
      () => {
        setState((current) => ({ ...current, error: "定位未授权，请手动输入出发点。" }));
      }
    );
  }

  return {
    ...state,
    setQuery,
    setInputMode,
    setIntent,
    setTargetDate,
    setStructuredField,
    detectOriginLocation,
    setQueryFromQuickReply: setQuery,
    submit
  };
}

function buildMessage(role: PlannerMessage["role"], content: string): PlannerMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    content
  };
}

function buildStructuredUserMessage(state: PlannerState): string {
  const constraints = state.structuredConstraints;
  const parts = [
    constraints.start_point ? `从${constraints.start_point}出发` : null,
    constraints.available_hours ? `骑${constraints.available_hours}小时` : null,
    constraints.target_distance_km ? `目标${constraints.target_distance_km}公里` : null,
    constraints.duration_bucket ? `时长偏好：${constraints.duration_bucket}` : null,
    constraints.overnight_preference ? `过夜偏好：${constraints.overnight_preference}` : null,
    constraints.lodging_preference ? `住宿：${constraints.lodging_preference}` : null,
    constraints.slope_tolerance ? `坡度：${constraints.slope_tolerance}` : null
  ].filter(Boolean);
  return parts.length > 0 ? `我补充一下：${parts.join("，")}。` : "我补充了规划条件。";
}

function buildPlannerRequest(state: PlannerState): PlannerRequest {
  return {
    intent: state.intent,
    query: state.inputMode === "natural" ? buildNaturalConversationQuery(state) : `表单规划：${state.structuredConstraints.origin_region ?? "杭州"}骑行`,
    target_date: state.targetDate,
    planning_mode: state.planningMode,
    planning_scene: state.planningScene,
    input_mode: state.inputMode,
    structured_constraints: state.inputMode === "structured" ? state.structuredConstraints : undefined
  };
}

function buildNaturalConversationQuery(state: PlannerState): string {
  return [
    ...state.messages.filter((message) => message.role === "user").map((message) => message.content),
    state.query.trim()
  ]
    .filter(Boolean)
    .join("；");
}

function parseNumber(value: string): number | undefined {
  const parsed = Number(value);
  return Number.isFinite(parsed) && value.trim() ? parsed : undefined;
}

function getExecutionContext(intent: RideIntent): { planningMode: PlanningMode; planningScene: PlanningScene } {
  if (intent === "weekend_recommendation") {
    return { planningMode: "nearby_trip", planningScene: "weekend_trip" };
  }
  return { planningMode: "route", planningScene: "city_ride" };
}

function getInitialQuery(intent: RideIntent): string {
  if (intent === "ride_plan") {
    return INITIAL_RIDE_PLAN_QUERY;
  }
  if (intent === "weekend_recommendation") {
    return INITIAL_NEARBY_QUERY;
  }
  return INITIAL_QUERY;
}

function getInitialAssistantMessage(intent: RideIntent): string {
  if (intent === "ride_plan") {
    return INITIAL_RIDE_PLAN_MESSAGE;
  }
  if (intent === "weekend_recommendation") {
    return INITIAL_WEEKEND_MESSAGE;
  }
  return INITIAL_CITY_MESSAGE;
}

function getLoadingLabel(intent: RideIntent): string {
  if (intent === "weekend_recommendation") {
    return "正在整理周末骑行出行方案";
  }
  if (intent === "ride_plan") {
    return "正在生成可执行骑行方案";
  }
  return "正在判断今天值不值得骑";
}

function resolveNextIntentState(intent: RideIntent): Pick<PlannerState, "intent" | "planningMode" | "planningScene"> {
  return {
    intent,
    ...getExecutionContext(intent),
  };
}
