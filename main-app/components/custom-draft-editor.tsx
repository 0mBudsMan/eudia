"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { AlertCircle } from "lucide-react"

interface CustomDraftEditorProps {
  value: string
  onChange: (value: string) => void
}

export function CustomDraftEditor({ value, onChange }: CustomDraftEditorProps) {
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [clientReady, setClientReady] = useState(false)
  const [autocompleteSuggestion, setAutocompleteSuggestion] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)
  const debounceTimer = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    const initializeClient = async () => {
      try {
        const { ensureGradioClient } = await import("@/lib/huggingface-service")
        await ensureGradioClient()
        setClientReady(true)
        console.log("[v0] Gradio client initialized successfully")
      } catch (error) {
        console.log("[v0] Failed to initialize Gradio client:", error)
        setClientReady(false)
      }
    }

    initializeClient()
  }, [])

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value
    onChange(newValue)
    setAutocompleteSuggestion("")

    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }

    const trimmedValue = newValue.trim()
    if (trimmedValue.length > 3 && clientReady) {
      setIsLoading(true)
      console.log("[v0] Requesting prediction for:", trimmedValue)
      debounceTimer.current = setTimeout(async () => {
        try {
          const { getNextWordPrediction } = await import("@/lib/huggingface-service")
          const predictions = await getNextWordPrediction(trimmedValue)
          console.log("[v0] Got predictions:", predictions)
          setSuggestions(predictions)
          if (predictions.length > 0) {
            setAutocompleteSuggestion(predictions[0])
            setShowSuggestions(true)
          } else {
            setShowSuggestions(false)
            setAutocompleteSuggestion("")
          }
          setIsLoading(false)
        } catch (error) {
          console.log("[v0] Prediction error:", error)
          setIsLoading(false)
        }
      }, 500)
    } else {
      setSuggestions([])
      setShowSuggestions(false)
      setAutocompleteSuggestion("")
    }
  }

  const insertSuggestion = (suggestion: string) => {
    if (!textareaRef.current) return

    const textarea = textareaRef.current
    const cursorPos = textarea.selectionStart
    const textBeforeCursor = value.substring(0, cursorPos)
    const textAfterCursor = value.substring(cursorPos)

    const newValue = textBeforeCursor + suggestion + " " + textAfterCursor
    onChange(newValue)

    setSuggestions([])
    setShowSuggestions(false)

    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.focus()
        textareaRef.current.setSelectionRange(cursorPos + suggestion.length + 1, cursorPos + suggestion.length + 1)
      }
    }, 0)
  }

  const acceptAutocomplete = () => {
    if (!autocompleteSuggestion || !textareaRef.current) return

    const textarea = textareaRef.current
    const cursorPos = textarea.selectionStart
    const textBeforeCursor = value.substring(0, cursorPos)
    const textAfterCursor = value.substring(cursorPos)

    const newValue = textBeforeCursor + autocompleteSuggestion + " "
    onChange(newValue)
    setAutocompleteSuggestion("")

    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.focus()
        textareaRef.current.setSelectionRange(
          cursorPos + autocompleteSuggestion.length + 1,
          cursorPos + autocompleteSuggestion.length + 1,
        )
      }
    }, 0)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Tab" && autocompleteSuggestion) {
      e.preventDefault()
      acceptAutocomplete()
    }
  }

  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current)
      }
    }
  }, [])

  return (
    <div className="space-y-4 relative">
      <div>
        <Label htmlFor="customDraft" className="text-sm font-medium text-foreground">
          Document Text
        </Label>
        <div className="relative">
          <Textarea
            ref={textareaRef}
            id="customDraft"
            value={value}
            onChange={handleTextChange}
            onKeyDown={handleKeyDown}
            placeholder="Paste or write your legal document here. You can then use the AI refinement chat to make improvements..."
            rows={15}
            className="font-mono text-sm resize-none"
          />

          {autocompleteSuggestion && (
            <div className="absolute top-0 left-0 pointer-events-none">
              <textarea
                value={value + autocompleteSuggestion + " "}
                disabled
                className="font-mono text-sm resize-none text-muted-foreground opacity-50 absolute top-0 left-0"
                rows={15}
                style={{
                  width: "100%",
                  height: "100%",
                  border: "none",
                  padding: "12px",
                  boxSizing: "border-box",
                  backgroundColor: "transparent",
                  color: "currentColor",
                }}
              />
            </div>
          )}

          {showSuggestions && suggestions.length > 0 && (
            <div
              ref={suggestionsRef}
              className="absolute bottom-2 left-2 bg-white border border-border rounded-lg shadow-lg z-10"
            >
              <div className="p-2">
                <p className="text-xs text-muted-foreground mb-2 font-medium">Next word suggestions:</p>
                <div className="space-y-1">
                  {suggestions.map((suggestion, index) => (
                    <Button
                      key={index}
                      onClick={() => insertSuggestion(suggestion)}
                      variant="outline"
                      size="sm"
                      className="w-full justify-start text-xs h-7"
                    >
                      {suggestion}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {isLoading && (
            <div className="absolute bottom-2 left-2 text-xs text-muted-foreground">Loading suggestions...</div>
          )}
        </div>
      </div>

      {!clientReady && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex gap-2">
          <AlertCircle className="h-4 w-4 text-yellow-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-yellow-900">
            Initializing AI next-word predictor... This may take a moment on first use.
          </p>
        </div>
      )}

      {clientReady && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex gap-2">
          <AlertCircle className="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-blue-900">
            <strong>Tip:</strong> Start typing or paste content above. The first AI suggestion appears grayed-out as you
            type—press Tab to accept it, or click other suggestions below to choose alternatives.
          </p>
        </div>
      )}
    </div>
  )
}

// Function to get next word prediction (not shown in the existing code)
// async function getNextWordPrediction(text: string): Promise<string[]> {
//   // Placeholder implementation
//   return ["example", "prediction", "words"]
// }
