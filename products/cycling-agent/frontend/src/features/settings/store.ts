/*
 * CN: 设置存储模块，同步用户画像到后端并保留 localStorage 降级。
 * EN: Settings store that syncs rider profile to the backend and keeps a localStorage fallback.
 */

export type UserProfile = {
  fitness_level: "low" | "medium" | "high" | "";
  slope_tolerance: "avoid" | "neutral" | "prefer" | "";
  ride_style_preferences: string[];
};

export type RiderState = {
  fatigue_level: "fresh" | "normal" | "tired" | "";
  mood: "relax" | "exercise" | "explore" | "social" | "recover" | "";
  last_ride_days_ago: number | "";
};

const STORAGE_KEY = "cycling-agent-user-profile";
const RIDER_STATE_STORAGE_KEY = "cycling-agent-rider-state";

export function loadUserProfile(): UserProfile {
  const storage = getStorage();
  if (!storage) {
    return emptyUserProfile();
  }

  const raw = storage.getItem(STORAGE_KEY);
  if (!raw) {
    return emptyUserProfile();
  }

  try {
    const parsed = JSON.parse(raw) as Partial<UserProfile>;
    return {
      fitness_level: parsed.fitness_level ?? "",
      slope_tolerance: parsed.slope_tolerance ?? "",
      ride_style_preferences: parsed.ride_style_preferences ?? []
    };
  } catch {
    return emptyUserProfile();
  }
}

export function loadRiderState(): RiderState {
  const storage = getStorage();
  if (!storage) {
    return emptyRiderState();
  }

  const raw = storage.getItem(RIDER_STATE_STORAGE_KEY);
  if (!raw) {
    return emptyRiderState();
  }

  try {
    const parsed = JSON.parse(raw) as Partial<RiderState>;
    return {
      fatigue_level: parsed.fatigue_level ?? "",
      mood: parsed.mood ?? "",
      last_ride_days_ago:
        typeof parsed.last_ride_days_ago === "number" && Number.isFinite(parsed.last_ride_days_ago) && parsed.last_ride_days_ago >= 0
          ? parsed.last_ride_days_ago
          : ""
    };
  } catch {
    return emptyRiderState();
  }
}


export function saveUserProfile(profile: UserProfile): void {
  const storage = getStorage();
  if (!storage) {
    return;
  }
  storage.setItem(STORAGE_KEY, JSON.stringify(profile));
}

export function saveRiderState(state: RiderState): void {
  const storage = getStorage();
  if (!storage) {
    return;
  }
  storage.setItem(RIDER_STATE_STORAGE_KEY, JSON.stringify(state));
}


export async function fetchUserProfile(): Promise<UserProfile | null> {
  const response = await fetch("/api/v1/profile/default");
  if (!response.ok) {
    throw new Error("profile-load-failed");
  }
  const payload = await response.json() as Partial<UserProfile>;
  if (!payload.fitness_level && !payload.slope_tolerance && !(payload.ride_style_preferences?.length)) {
    return null;
  }
  return {
    fitness_level: payload.fitness_level ?? "",
    slope_tolerance: payload.slope_tolerance ?? "",
    ride_style_preferences: payload.ride_style_preferences ?? []
  };
}


export async function persistUserProfile(profile: UserProfile): Promise<UserProfile> {
  const response = await fetch("/api/v1/profile/default", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile)
  });
  if (!response.ok) {
    throw new Error("profile-save-failed");
  }
  const payload = await response.json() as Partial<UserProfile>;
  return {
    fitness_level: payload.fitness_level ?? "",
    slope_tolerance: payload.slope_tolerance ?? "",
    ride_style_preferences: payload.ride_style_preferences ?? []
  };
}


function emptyUserProfile(): UserProfile {
  return {
    fitness_level: "",
    slope_tolerance: "",
    ride_style_preferences: []
  };
}

function emptyRiderState(): RiderState {
  return {
    fatigue_level: "",
    mood: "",
    last_ride_days_ago: ""
  };
}


function getStorage(): Pick<Storage, "getItem" | "setItem"> | null {
  if (typeof window === "undefined") {
    return null;
  }

  const candidate = window.localStorage;
  if (
    !candidate ||
    typeof candidate.getItem !== "function" ||
    typeof candidate.setItem !== "function"
  ) {
    return null;
  }

  return candidate;
}
