export type LifestyleProfile = {
  home_region: string | null;
  preferred_vibe: string | null;
  companion_tone: string | null;
  favorite_motifs: string[];
  avoid_motifs: string[];
};

export async function getLifestyleProfile(): Promise<LifestyleProfile> {
  return fetchJson("/api/v1/profile/lifestyle");
}

export async function saveLifestyleProfile(profile: LifestyleProfile): Promise<LifestyleProfile> {
  return fetchJson("/api/v1/profile/lifestyle", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(`request-failed:${url}`);
  }
  return response.json() as Promise<T>;
}
