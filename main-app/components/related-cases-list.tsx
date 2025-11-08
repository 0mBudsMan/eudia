"use client"
import CaseCard from "./case-card"
import type { RelatedCase, CaseDetails } from "@/lib/api-simulations"

interface RelatedCasesListProps {
  cases: RelatedCase[]
  onCaseSelected: (caseDetails: CaseDetails) => void
  onCaseAnalyzed: (updatedCase: RelatedCase) => void
}

export default function RelatedCasesList({ cases, onCaseSelected, onCaseAnalyzed }: RelatedCasesListProps) {
  const analyzedCases = cases.slice(0, 10)
  const unanalyzedCases = cases.slice(10)

  return (
    <div className="space-y-8">
      {/* First 10 cases with verdicts */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-foreground">Initial Analysis Results</h3>
        <div className="grid gap-4 md:grid-cols-2">
          {analyzedCases.map((caseItem) => (
            <CaseCard
              key={caseItem.id}
              caseItem={caseItem}
              onCaseSelected={onCaseSelected}
              onCaseAnalyzed={onCaseAnalyzed}
            />
          ))}
        </div>
      </div>

      {/* Remaining cases with analyze buttons */}
      {unanalyzedCases.length > 0 && (
        <div>
          <h3 className="mb-4 text-lg font-semibold text-foreground">
            Additional Related Cases ({unanalyzedCases.length})
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {unanalyzedCases.map((caseItem) => (
              <CaseCard
                key={caseItem.id}
                caseItem={caseItem}
                onCaseSelected={onCaseSelected}
                onCaseAnalyzed={onCaseAnalyzed}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
