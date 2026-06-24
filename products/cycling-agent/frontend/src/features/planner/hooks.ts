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
  PlanningMode,
  PlanningScene,
  RidePlanResponse,
  StructuredConstraints
} from "./api";
import { loadRiderState, loadUserProfile, saveRiderState, type RiderState } from "../settings/store";

type PlannerState = {
  messages: PlannerMessage[];
  query: string;
  planningMode: PlanningMode;
  planningScene: PlanningScene;
  inputMode: InputMode;
  targetDate: string;
  structuredConstraints: StructuredConstraints;
  slotState: Record<string, unknown>;
  riderState: RiderState;
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
const INITIAL_NEARBY_QUERY = "周末想出去骑车，附近有什么推荐线路么";
const INITIAL_CITY_MESSAGE = "嗨，我是 AAA骑车帮帮。你可以直接说“我今天晚上想出去骑行一下”，我会像朋友一样帮你判断今晚适不适合骑。";
const INITIAL_WEEKEND_MESSAGE = "嗨，我是 AAA骑车帮帮。周末想出去骑车也可以直接说，我会帮你看目的地、天数、住宿和返程。";
const DEFAULT_QUICK_REPLIES = ["今晚轻松骑", "现在出发", "不要爬坡", "骑 2 小时", "周末两天", "千岛湖"];

type UsePlannerFlowOptions = {
  onSuccess?: (result: RidePlanResponse) => void;
};

export function usePlannerFlow(options?: UsePlannerFlowOptions) {
  const [state, setState] = useState<PlannerState>({
    messages: [buildMessage("assistant", INITIAL_CITY_MESSAGE)],
    query: INITIAL_QUERY,
    planningMode: "route",
    planningScene: "city_ride",
    inputMode: "natural",
    targetDate: formatLocalDate(new Date()),
    structuredConstraints: createEmptyStructuredConstraints(),
    slotState: {},
    riderState: loadRiderState(),
    quickReplies: DEFAULT_QUICK_REPLIES,
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
      loadingLabel: state.inputMode === "natural" ? "AAA骑车帮帮正在理解你的想法" : state.planningScene === "weekend_trip" ? "正在生成周末骑行出行方案" : "正在生成今晚骑行建议",
      error: null,
      result: null,
      clarificationPrompt: null,
      stageUpdates: []
    }));

    try {
      const userProfile = loadUserProfile();
      const riderState = state.riderState;
      if (state.inputMode === "natural") {
        const chatMessages: ChatTurnMessage[] = [
          ...state.messages.map((message) => ({ role: message.role, content: message.content })),
          { role: "user", content: submittedText }
        ];
        const chatTurn = await createChatTurn(
          {
            messages: chatMessages,
            planning_scene: state.planningScene,
            target_date: state.targetDate,
            slot_state: state.slotState
          },
          userProfile,
          riderState
        );

        if (!chatTurn.ready_to_plan || !chatTurn.planner_request) {
          setState((current) => ({
            ...current,
            slotState: chatTurn.slot_state,
            quickReplies: chatTurn.ui_hints?.quick_replies?.length ? chatTurn.ui_hints.quick_replies : DEFAULT_QUICK_REPLIES,
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
          slotState: chatTurn.slot_state,
          quickReplies: chatTurn.ui_hints?.quick_replies?.length ? chatTurn.ui_hints.quick_replies : DEFAULT_QUICK_REPLIES,
          messages: [...current.messages, buildMessage("assistant", chatTurn.assistant_message)],
          loadingLabel: chatTurn.ui_hints?.planning_status_label ?? "我在看天气和路线难度"
        }));
        const result = await createRidePlanStream(chatTurn.planner_request, userProfile, riderState, {
          onStage: (stage) => {
            setState((current) => ({
              ...current,
              stageUpdates: [...current.stageUpdates, stage]
            }));
          }
        }).catch(async () => createRidePlan(chatTurn.planner_request as PlannerRequest, userProfile, riderState));
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
      setState((current) => ({ ...current, loadingLabel: state.planningScene === "weekend_trip" ? "正在生成周末骑行出行方案" : "正在生成今晚骑行建议" }));
      const result = await createRidePlanStream(request, userProfile, riderState, {
        onStage: (stage) => {
          setState((current) => ({
            ...current,
            stageUpdates: [...current.stageUpdates, stage]
          }));
        }
      }).catch(async () => createRidePlan(request, userProfile, riderState));
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

  function setPlanningMode(planningMode: PlanningMode) {
    const planningScene: PlanningScene = planningMode === "nearby_trip" ? "weekend_trip" : "city_ride";
    setState((current) => ({
      ...current,
      planningMode,
      planningScene,
      query: planningMode === "nearby_trip" ? INITIAL_NEARBY_QUERY : INITIAL_QUERY,
      messages: [buildMessage("assistant", planningMode === "nearby_trip" ? INITIAL_WEEKEND_MESSAGE : INITIAL_CITY_MESSAGE)],
      slotState: {},
      quickReplies: DEFAULT_QUICK_REPLIES,
      inputMode: "natural",
      targetDate: formatLocalDate(new Date()),
      structuredConstraints: createEmptyStructuredConstraints(),
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

  function setRiderStateField(field: keyof RiderState, value: RiderState[keyof RiderState]) {
    setState((current) => {
      const nextRiderState = {
        ...current.riderState,
        [field]: field === "last_ride_days_ago" && value !== "" ? Number(value) : value
      } as RiderState;
      saveRiderState(nextRiderState);
      return {
        ...current,
        riderState: nextRiderState
      };
    });
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
    setPlanningMode,
    setTargetDate,
    setStructuredField,
    setRiderStateField,
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

function createEmptyStructuredConstraints(): StructuredConstraints {
  return {
    destination_preferences: []
  };
}

function formatLocalDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
