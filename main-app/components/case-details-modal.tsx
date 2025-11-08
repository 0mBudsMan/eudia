"use client"

import { useEffect, useState } from "react"
import { Dialog } from "@headlessui/react"
import { fetchCaseDetails, type CaseDetails } from "@/lib/api-simulations"

interface CaseDetailsModalProps {
  caseId: string
  isOpen: boolean
  onClose: () => void
  caseDetails: CaseDetails | null
  isLoading: boolean
}

export default function CaseDetailsModal({
  caseId,
  isOpen,
  onClose,
  caseDetails: initialDetails,
  isLoading: initialLoading,
}: CaseDetailsModalProps) {
  const [details, setDetails] = useState<CaseDetails | null>(initialDetails)
  const [loading, setLoading] = useState(initialLoading)

  useEffect(() => {
    if (isOpen && !details) {
      setLoading(true)
      fetchCaseDetails(caseId)
        .then(setDetails)
        .catch(console.error)
        .finally(() => setLoading(false))
    }
  }, [isOpen, caseId, details])

  const getVerdictColor = (type: "in-favor" | "against" | "neutral") => {
    switch (type) {
      case "in-favor":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100"
      case "against":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100"
      case "neutral":
        return "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-100"
    }
  }

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-lg bg-card shadow-xl border border-border">
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <div className="flex flex-col items-center gap-2">
                <svg
                  className="h-8 w-8 animate-spin text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <p className="text-sm text-muted-foreground">Loading case details...</p>
              </div>
            </div>
          ) : details ? (
            <div className="p-8">
              {/* Header */}
              <div className="mb-6 flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-semibold text-muted-foreground">{details.caseNumber}</p>
                  <h2 className="mt-2 text-2xl font-bold text-foreground">{details.title}</h2>
                </div>
                <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Verdict Badge */}
              <div className="mb-6 flex items-center gap-4">
                <div
                  className={`rounded-full px-4 py-2 text-sm font-semibold ${getVerdictColor(details.verdict.type)}`}
                >
                  {details.verdict.label}
                </div>
                <span className="text-sm text-muted-foreground">
                  Relevance Score: {(details.relevanceScore * 100).toFixed(0)}%
                </span>
              </div>

              {/* Case Information */}
              <div className="mb-6 grid grid-cols-2 gap-4 rounded-lg bg-muted p-4">
                <div>
                  <p className="text-xs font-semibold text-muted-foreground">COURT</p>
                  <p className="mt-1 text-sm font-medium text-foreground">{details.court}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-muted-foreground">YEAR</p>
                  <p className="mt-1 text-sm font-medium text-foreground">{details.year}</p>
                </div>
              </div>

              {/* Summary */}
              <div className="mb-6">
                <h3 className="mb-2 font-semibold text-foreground">SUMMARY</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{details.summary}</p>
              </div>

              {/* Key Points */}
              <div className="mb-6">
                <h3 className="mb-3 font-semibold text-foreground">KEY POINTS</h3>
                <ul className="space-y-2">
                  {details.keyPoints.map((point, idx) => (
                    <li key={idx} className="flex gap-3 text-sm text-muted-foreground">
                      <span className="font-semibold text-primary">•</span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Judges */}
              <div className="mb-6">
                <h3 className="mb-3 font-semibold text-foreground">JUDGES</h3>
                <div className="space-y-1">
                  {details.judges.map((judge, idx) => (
                    <p key={idx} className="text-sm text-muted-foreground">
                      {judge}
                    </p>
                  ))}
                </div>
              </div>

              {/* Citations */}
              <div className="mb-6">
                <h3 className="mb-3 font-semibold text-foreground">CITATIONS</h3>
                <div className="space-y-1 rounded-lg bg-muted p-3">
                  {details.citations.map((citation, idx) => (
                    <p key={idx} className="font-mono text-xs text-muted-foreground">
                      {citation}
                    </p>
                  ))}
                </div>
              </div>

              {/* Close Button */}
              <button
                onClick={onClose}
                className="w-full rounded-md bg-primary px-4 py-2 font-semibold text-primary-foreground hover:bg-primary/90"
              >
                Close
              </button>
            </div>
          ) : (
            <div className="p-8 text-center">
              <p className="text-muted-foreground">No case details available</p>
            </div>
          )}
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}
