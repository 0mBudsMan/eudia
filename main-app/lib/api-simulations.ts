const API_BASE_URL = process.env.NEXT_PUBLIC_RESEARCH_API_URL ?? "http://localhost:8000"

export interface Verdict {
  type: "in-favor" | "against" | "neutral"
  label: string
}

export interface RelatedCase {
  id: string
  caseNumber: string
  title: string
  year: number
  court: string
  verdict?: Verdict | null
  isAnalyzed: boolean
  analysisSummary?: string | null
}

export interface CaseDetails {
  id: string
  caseNumber: string
  title: string
  year: number
  court: string
  judges: string[]
  verdict: Verdict
  summary: string
  keyPoints: string[]
  citations: string[]
  relevanceScore: number
  excerpt?: string | null
}

interface CaseBriefResponse {
  cases: RelatedCase[]
  verdictSummary: {
    wins: number
    losses: number
    unclear: number
  }
  antiArguments?: string
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

// API 1: Submit case brief to backend
export async function submitCaseBrief(briefText: string): Promise<RelatedCase[]> {
  const response = await fetch(`${API_BASE_URL}/api/research/brief`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ case_input: briefText }),
  })

  const data = await handleResponse<CaseBriefResponse>(response)
  return data.cases
}

// API 2: Ask backend to analyze a case without verdict information
export async function analyzeCase(caseId: string): Promise<Verdict> {
  const response = await fetch(`${API_BASE_URL}/api/research/cases/${caseId}/analyze`, {
    method: "POST",
  })
  const data = await handleResponse<{ verdict: Verdict }>(response)
  return data.verdict
}

// API 3: Fetch complete case details from backend
export async function fetchCaseDetails(caseId: string): Promise<CaseDetails> {
  const response = await fetch(`${API_BASE_URL}/api/research/cases/${caseId}`)
  return handleResponse<CaseDetails>(response)
}
