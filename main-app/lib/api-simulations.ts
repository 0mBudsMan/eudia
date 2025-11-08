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
  verdict?: Verdict
  isAnalyzed: boolean
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
}

// Mock data for related cases
const mockCases: RelatedCase[] = [
  {
    id: "1",
    caseNumber: "CA-2023-001",
    title: "Smith v. Corporation Inc.",
    year: 2023,
    court: "California Supreme Court",
    verdict: { type: "in-favor", label: "In Favor" },
    isAnalyzed: true,
  },
  {
    id: "2",
    caseNumber: "NY-2023-045",
    title: "Johnson et al. v. State Board",
    year: 2023,
    court: "New York Court of Appeals",
    verdict: { type: "against", label: "Against Us" },
    isAnalyzed: true,
  },
  {
    id: "3",
    caseNumber: "TX-2022-089",
    title: "Brown v. Federal Agency",
    year: 2022,
    court: "U.S. District Court, Texas",
    verdict: { type: "neutral", label: "Settled" },
    isAnalyzed: true,
  },
  {
    id: "4",
    caseNumber: "FL-2023-012",
    title: "Martinez v. Private Firm",
    year: 2023,
    court: "Florida Court of Appeals",
    verdict: { type: "in-favor", label: "In Favor" },
    isAnalyzed: true,
  },
  {
    id: "5",
    caseNumber: "IL-2023-056",
    title: "Davis & Associates v. Municipality",
    year: 2023,
    court: "Illinois Supreme Court",
    verdict: { type: "against", label: "Against Us" },
    isAnalyzed: true,
  },
  {
    id: "6",
    caseNumber: "PA-2022-134",
    title: "Williams v. Healthcare Corp",
    year: 2022,
    court: "Pennsylvania Superior Court",
    verdict: { type: "neutral", label: "Settled" },
    isAnalyzed: true,
  },
  {
    id: "7",
    caseNumber: "OH-2023-078",
    title: "Taylor v. Education Board",
    year: 2023,
    court: "Ohio Supreme Court",
    verdict: { type: "in-favor", label: "In Favor" },
    isAnalyzed: true,
  },
  {
    id: "8",
    caseNumber: "MI-2023-102",
    title: "Anderson v. Insurance Company",
    year: 2023,
    court: "Michigan Court of Appeals",
    verdict: { type: "against", label: "Against Us" },
    isAnalyzed: true,
  },
  {
    id: "9",
    caseNumber: "GA-2022-067",
    title: "Thompson v. Financial Institution",
    year: 2022,
    court: "Georgia Supreme Court",
    verdict: { type: "neutral", label: "Settled" },
    isAnalyzed: true,
  },
  {
    id: "10",
    caseNumber: "NC-2023-091",
    title: "Jackson v. Transportation Authority",
    year: 2023,
    court: "North Carolina Court of Appeals",
    verdict: { type: "in-favor", label: "In Favor" },
    isAnalyzed: true,
  },
  // Remaining cases without analyzed verdicts
  {
    id: "11",
    caseNumber: "WA-2023-145",
    title: "White v. Technology Company",
    year: 2023,
    court: "Washington Supreme Court",
    isAnalyzed: false,
  },
  {
    id: "12",
    caseNumber: "CO-2023-167",
    title: "Harris v. Mining Corporation",
    year: 2023,
    court: "Colorado Court of Appeals",
    isAnalyzed: false,
  },
  {
    id: "13",
    caseNumber: "AZ-2023-189",
    title: "Lee v. Real Estate Developer",
    year: 2023,
    court: "Arizona Supreme Court",
    isAnalyzed: false,
  },
  {
    id: "14",
    caseNumber: "MA-2023-203",
    title: "Martin v. Research Institution",
    year: 2023,
    court: "Massachusetts Court of Appeals",
    isAnalyzed: false,
  },
  {
    id: "15",
    caseNumber: "MO-2023-218",
    title: "Garcia v. Public Utility",
    year: 2023,
    court: "Missouri Supreme Court",
    isAnalyzed: false,
  },
]

// API 1: Process case brief and return related cases
export async function submitCaseBrief(briefText: string, _file?: File): Promise<RelatedCase[]> {
  // Simulate API call delay
  await new Promise((resolve) => setTimeout(resolve, 800))

  // In a real app, this would send briefText and file to backend
  console.log("[API] Processing case brief:", briefText.substring(0, 50) + "...")

  // Return mock related cases
  return mockCases
}

// API 2: Analyze a case (for cases without verdicts)
export async function analyzeCase(caseId: string): Promise<Verdict> {
  // Simulate API call delay
  await new Promise((resolve) => setTimeout(resolve, 1200))

  console.log("[API] Analyzing case:", caseId)

  // Generate a random verdict for simulation
  const verdicts: Verdict[] = [
    { type: "in-favor", label: "In Favor" },
    { type: "against", label: "Against Us" },
    { type: "neutral", label: "Settled" },
  ]

  return verdicts[Math.floor(Math.random() * verdicts.length)]
}

// API 3: Fetch complete case details
export async function fetchCaseDetails(caseId: string): Promise<CaseDetails> {
  // Simulate API call delay
  await new Promise((resolve) => setTimeout(resolve, 600))

  console.log("[API] Fetching case details:", caseId)

  const relatedCase = mockCases.find((c) => c.id === caseId)

  if (!relatedCase) {
    throw new Error("Case not found")
  }

  // Create detailed case information
  const verdict = relatedCase.verdict || { type: "neutral", label: "Pending" }

  const caseDetails: CaseDetails = {
    id: relatedCase.id,
    caseNumber: relatedCase.caseNumber,
    title: relatedCase.title,
    year: relatedCase.year,
    court: relatedCase.court,
    judges: ["Hon. Judge Smith", "Hon. Judge Johnson", "Hon. Judge Williams"],
    verdict,
    summary: `This case involves a legal dispute related to ${relatedCase.title.split(" v. ")[1]}. The proceedings took place in ${relatedCase.court} during ${relatedCase.year}. The case addresses key legal principles and established important precedent in the jurisdiction.`,
    keyPoints: [
      "Established precedent for contractual interpretation",
      "Clarified jurisdiction over interstate disputes",
      "Set standards for damages calculation",
      "Addressed liability in commercial transactions",
    ],
    citations: [
      `${relatedCase.caseNumber} (${relatedCase.year})`,
      "42 U.S.C. § 1983",
      "Fed. R. Civ. P. 56",
      "Rules of Civil Procedure, Section 12(b)(6)",
    ],
    relevanceScore: 0.85 + Math.random() * 0.15, // 85-100%
  }

  return caseDetails
}
