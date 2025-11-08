"use client"

import Link from "next/link"
import { useState } from "react"
import CaseBriefForm from "@/components/case-brief-form"
import RelatedCasesList from "@/components/related-cases-list"
import CaseDetailsModal from "@/components/case-details-modal"
import { Button } from "@/components/ui/button"
import type { RelatedCase, CaseDetails } from "@/lib/api-simulations"

export default function Home() {
  const [cases, setCases] = useState<RelatedCase[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)
  const [caseDetails, setCaseDetails] = useState<CaseDetails | null>(null)
  const [detailsLoading, setDetailsLoading] = useState(false)

  const handleCaseSubmitted = (newCases: RelatedCase[]) => {
    setCases(newCases)
    setLoading(false)
  }

  const handleCaseAnalyzed = (updatedCase: RelatedCase) => {
    setCases((prev) => prev.map((c) => (c.id === updatedCase.id ? updatedCase : c)))
  }

  const handleCaseSelected = (caseDetails: CaseDetails) => {
    setCaseDetails(caseDetails)
    setSelectedCaseId(caseDetails.id)
  }

  return (
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card shadow-sm">
        <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-primary">Legal Case Analyzer</h1>
              <p className="mt-1 text-sm text-muted-foreground">Automated legal process analysis and case research</p>
            </div>
            <div className="flex items-center gap-3">
              <Button asChild variant="outline" className="border-primary text-primary hover:bg-primary/10">
                <Link href="/contracts">Open Contract Workspace</Link>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        {cases.length === 0 ? (
          // Initial state - show form
          <CaseBriefForm onSubmit={handleCaseSubmitted} isLoading={loading} setLoading={setLoading} />
        ) : (
          // Results state - show cases and form
          <div className="space-y-8">
            {/* Results summary */}
            <div className="rounded-lg border border-border bg-card p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-foreground">Related Cases Found</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {cases.length} cases matched your search criteria
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-primary">{cases.length}</p>
                  <p className="text-xs text-muted-foreground">total cases</p>
                </div>
              </div>
            </div>

            {/* Cases list */}
            <RelatedCasesList cases={cases} onCaseSelected={handleCaseSelected} onCaseAnalyzed={handleCaseAnalyzed} />

            {/* New search form */}
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="mb-4 text-lg font-semibold text-foreground">Perform Another Search</h3>
              <CaseBriefForm onSubmit={handleCaseSubmitted} isLoading={loading} setLoading={setLoading} />
            </div>
          </div>
        )}
      </div>

      {/* Case Details Modal */}
      {selectedCaseId && (
        <CaseDetailsModal
          caseId={selectedCaseId}
          isOpen={!!selectedCaseId}
          onClose={() => {
            setSelectedCaseId(null)
            setCaseDetails(null)
          }}
          caseDetails={caseDetails}
          isLoading={detailsLoading}
        />
      )}
    </main>
  )
}
