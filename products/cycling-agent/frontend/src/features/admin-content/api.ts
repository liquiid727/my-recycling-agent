import type { ExperienceContent } from "../experience/api";

export async function getExperienceContent(): Promise<ExperienceContent> {
  return fetchJson("/api/v1/admin/experience-content");
}

export async function saveExperienceContent(content: ExperienceContent): Promise<ExperienceContent> {
  return fetchJson("/api/v1/admin/experience-content", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(content),
  });
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(`request-failed:${url}`);
  }
  return response.json() as Promise<T>;
}
