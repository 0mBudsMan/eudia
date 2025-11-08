"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { submitCaseBrief } from "@/lib/api-simulations"

interface CaseBriefFormProps {
  onSubmit: (cases: any[]) => void
  isLoading: boolean
  setLoading: (loading: boolean) => void
}

export default function CaseBriefForm({ onSubmit, isLoading, setLoading }: CaseBriefFormProps) {
  const [briefText, setBriefText] = useState("")
  const [activeTab, setActiveTab] = useState<"text" | "file">("text")
  const [fileName, setFileName] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setFileName(file.name)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!briefText.trim()) {
      alert("Please enter a case brief or upload a file")
      return
    }

    setLoading(true)
    try {
      const results = await submitCaseBrief(briefText)
      onSubmit(results)
    } catch (error) {
      console.error("Error submitting case brief:", error)
      alert("Error processing case brief. Please try again.")
      setLoading(false)
    }
  }

  return (
    <Card className="border-2 border-primary p-8">
      <h2 className="mb-2 text-2xl font-bold text-primary">STEP 1: CASE BRIEF</h2>
      <p className="mb-6 text-sm text-muted-foreground">
        Enter your case brief in text format or upload a document file (.pdf, .docx, .txt)
      </p>

      {/* Tabs */}
      <div className="mb-6 flex gap-2">
        <button
          onClick={() => setActiveTab("text")}
          className={`rounded-md px-4 py-2 font-semibold transition-colors ${
            activeTab === "text"
              ? "bg-primary text-primary-foreground"
              : "border border-border bg-background text-foreground hover:bg-muted"
          }`}
        >
          Enter Text
        </button>
        <button
          onClick={() => setActiveTab("file")}
          className={`rounded-md px-4 py-2 font-semibold transition-colors ${
            activeTab === "file"
              ? "bg-primary text-primary-foreground"
              : "border border-border bg-background text-foreground hover:bg-muted"
          }`}
        >
          Upload File
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {activeTab === "text" ? (
          <>
            <div>
              <label className="block text-sm font-medium text-foreground">Case Brief Text</label>
              <textarea
                value={briefText}
                onChange={(e) => setBriefText(e.target.value)}
                placeholder="Enter your case brief here. Include key facts, legal issues, and relevant information..."
                className="mt-2 w-full rounded-md border-2 border-primary bg-input p-4 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                rows={8}
              />
            </div>
          </>
        ) : (
          <>
            <div className="rounded-md border-2 border-dashed border-primary p-8 text-center">
              <input
                type="file"
                id="file-upload"
                className="hidden"
                onChange={handleFileChange}
                accept=".pdf,.docx,.txt"
              />
              <label htmlFor="file-upload" className="flex flex-col items-center gap-2 cursor-pointer">
                <svg className="h-12 w-12 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span className="font-semibold text-primary">{fileName || "Click to upload or drag and drop"}</span>
                <span className="text-xs text-muted-foreground">PDF, DOCX, or TXT files up to 10MB</span>
              </label>
            </div>
            <div className="rounded-md border border-border bg-muted p-4">
              <p className="text-sm text-muted-foreground">
                Note: File content will be analyzed and used to find related cases.
              </p>
            </div>
          </>
        )}

        <Button
          type="submit"
          disabled={isLoading}
          className="w-full bg-accent px-6 py-3 font-semibold text-accent-foreground hover:bg-accent/90 disabled:opacity-50"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="h-4 w-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Analyzing...
            </span>
          ) : (
            "Analyze Case"
          )}
        </Button>
      </form>
    </Card>
  )
}
