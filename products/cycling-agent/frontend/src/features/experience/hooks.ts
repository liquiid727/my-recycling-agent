import { useEffect, useState } from "react";

import {
  createCompanionPlan,
  getExperienceHome,
  getExperienceResult,
  getExperienceRoute,
  type CompanionPlanResponse,
  type ExperienceContent,
  type ExperienceResult,
  type ExperienceRouteDetail,
} from "./api";
import { loadUserProfile } from "../settings/store";

export function useExperienceHome() {
  const [content, setContent] = useState<ExperienceContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void getExperienceHome()
      .then((payload) => {
        if (!active) return;
        setContent(payload);
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setError("首页内容暂时不可用，请稍后再试。");
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  return { content, loading, error };
}

export function useCompanionPlan() {
  const [submitting, setSubmitting] = useState(false);
  const [response, setResponse] = useState<CompanionPlanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(message: string) {
    setSubmitting(true);
    setError(null);
    try {
      const userProfile = loadUserProfile();
      const payload = await createCompanionPlan({
        message,
        target_date: formatLocalDate(new Date()),
        user_profile: hasRiderProfile(userProfile)
          ? {
              fitness_level: userProfile.fitness_level || undefined,
              slope_tolerance: userProfile.slope_tolerance || undefined,
              ride_style_preferences: userProfile.ride_style_preferences,
            }
          : undefined,
      });
      setResponse(payload);
    } catch {
      setError("AI 伙伴暂时没有接住这句心情，请稍后再试。");
    } finally {
      setSubmitting(false);
    }
  }

  return { submitting, response, error, submit };
}

export function useExperienceResult(requestNo: string) {
  const [result, setResult] = useState<ExperienceResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    void getExperienceResult(requestNo)
      .then((payload) => {
        if (!active) return;
        setResult(payload);
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setError("这页骑行结果暂时翻不开，请回首页重新生成。");
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [requestNo]);

  return { result, loading, error };
}

export function useExperienceRouteDetail(routeCode: string) {
  const [routeDetail, setRouteDetail] = useState<ExperienceRouteDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    void getExperienceRoute(routeCode)
      .then((payload) => {
        if (!active) return;
        setRouteDetail(payload);
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setError("这条路线的手账页暂时不可用。");
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [routeCode]);

  return { routeDetail, loading, error };
}

function hasRiderProfile(userProfile: ReturnType<typeof loadUserProfile>) {
  return Boolean(userProfile.fitness_level || userProfile.slope_tolerance || userProfile.ride_style_preferences.length > 0);
}

function formatLocalDate(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
