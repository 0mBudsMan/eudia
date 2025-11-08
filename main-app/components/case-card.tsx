"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { analyzeCase, fetchCaseDetails, type RelatedCase, type CaseDetails } from "@/lib/api-simulations"

interface CaseCardProps {
  caseItem: RelatedCase
  onCaseSelected: (caseDetails: CaseDetails) => void
  onCaseAnalyzed: (updatedCase: RelatedCase) => void
}

export default function CaseCard({ caseItem, onCaseSelected, onCaseAnalyzed }: CaseCardProps) {
  const [analyzing, setAnalyzing] = useState(false)
  const [loading, setLoading] = useState(false)

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

  const handleAnalyze = async () => {
    setAnalyzing(true)
    try {
      const verdict = await analyzeCase(caseItem.id)
      onCaseAnalyzed({
        ...caseItem,
        verdict,
        isAnalyzed: true,
      })
    } catch (error) {
      console.error("Error analyzing case:", error)
      alert("Error analyzing case. Please try again.")
    } finally {
      setAnalyzing(false)
    }
  }

  const handleViewDetails = async () => {
    setLoading(true)
    try {
      const details = await fetchCaseDetails(caseItem.id)
      onCaseSelected(details)
    } catch (error) {
      console.error("Error fetching case details:", error)
      alert("Error loading case details. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card
      onClick={handleViewDetails}
      className="cursor-pointer border-2 border-border transition-all hover:border-primary hover:shadow-lg"
    >
      <div className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-muted-foreground">{caseItem.caseNumber}</p>
            <h4 className="mt-1 text-lg font-semibold text-foreground truncate">{caseItem.title}</h4>
            <p className="mt-2 text-sm text-muted-foreground">{caseItem.court}</p>
            <p className="text-xs text-muted-foreground">{caseItem.year}</p>
          </div>

          {caseItem.verdict && (
            <div
              className={`flex-shrink-0 rounded-full px-3 py-1 text-sm font-semibold ${getVerdictColor(caseItem.verdict.type)}`}
            >
              {caseItem.verdict.label}
            </div>
          )}
        </div>

        <div className="mt-4 flex gap-2">
          {!caseItem.isAnalyzed ? (
            <Button
              onClick={(e) => {
                e.stopPropagation()
                handleAnalyze()
              }}
              disabled={analyzing}
              className="flex-1 bg-accent text-accent-foreground hover:bg-accent/90 disabled:opacity-50"
            >
              {analyzing ? "Analyzing..." : "Analyze"}
            </Button>
          ) : (
            <Button
              onClick={(e) => {
                e.stopPropagation()
                handleViewDetails()
              }}
              disabled={loading}
              className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {loading ? "Loading..." : "View Details"}
            </Button>
          )}
        </div>
      </div>
    </Card>
  )
}
