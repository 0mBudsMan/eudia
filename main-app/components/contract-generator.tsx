"use client"

import { useEffect, useState } from "react"
import { ContractForm } from "./contract-form"
import { ContractPreview } from "./contract-preview"
import { ContractChat } from "./contract-chat"
import { ExportMenu } from "./export-menu"
import { Button } from "@/components/ui/button"
import { FileText, Zap, MessageCircle, Briefcase, Edit3 } from "lucide-react"
import { generateContractWithGemini } from "@/lib/gemini-service"
import { saveContract, type SavedContract } from "@/lib/contract-storage"

interface ContractGeneratorProps {
  selectedContract?: SavedContract
}

const buildFormData = (contract?: SavedContract) => ({
  partyA: contract?.partyA || "",
  partyB: contract?.partyB || "",
  duration: contract?.duration || "2 years",
  scope: "",
  serviceScope: "",
  compensation: "",
  paymentTerms: "Net 30",
  restrictions: [],
  jurisdiction: contract?.jurisdiction || "California",
  companyName: "",
  companyAddress: "",
  employeeName: "",
  employeeEmail: "",
  jobTitle: "",
  department: "",
  salary: "",
  startDate: "",
  employmentType: "Full-time",
  reportsTo: "",
  benefits: "",
  customDraft: contract?.content || "",
})

export function ContractGenerator({ selectedContract }: ContractGeneratorProps) {
  const [contract, setContract] = useState<string>(selectedContract?.content || "")
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string>("")
  const [showChat, setShowChat] = useState(false)
  const [contractType, setContractType] = useState<"nda" | "service-agreement" | "employment-offer" | "custom-draft">(
    "nda",
  )
  const [formData, setFormData] = useState(() => buildFormData(selectedContract))
  const [activeContractId, setActiveContractId] = useState<string | undefined>(selectedContract?.id)
  const [activeContractCreatedAt, setActiveContractCreatedAt] = useState<Date | undefined>(
    selectedContract?.createdAt ? new Date(selectedContract.createdAt) : undefined
  )

  const handleContractTypeChange = (type: "nda" | "service-agreement" | "employment-offer" | "custom-draft") => {
    setContractType(type)
    setContract("")
    setError("")
  }

  const generateContractId = () => {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      return crypto.randomUUID()
    }
    return Math.random().toString(36).slice(2)
  }

  const persistContract = (content: string, metadata: typeof formData) => {
    if (!metadata.partyA?.trim() || !metadata.partyB?.trim()) {
      return
    }

    const record: SavedContract = {
      id: activeContractId || generateContractId(),
      partyA: metadata.partyA.trim(),
      partyB: metadata.partyB.trim(),
      jurisdiction: metadata.jurisdiction || "Unspecified",
      duration: metadata.duration || "Unspecified",
      content,
      createdAt: activeContractCreatedAt || new Date(),
      updatedAt: new Date(),
    }

    saveContract(record)
    setActiveContractId(record.id)
    setActiveContractCreatedAt(record.createdAt)
  }

  useEffect(() => {
    if (selectedContract) {
      setContract(selectedContract.content)
      setShowChat(true)
      setContractType("custom-draft")
      setFormData(buildFormData(selectedContract))
      setActiveContractId(selectedContract.id)
      setActiveContractCreatedAt(selectedContract.createdAt ? new Date(selectedContract.createdAt) : undefined)
    } else {
      setFormData(buildFormData())
      setContract("")
      setShowChat(false)
      setContractType("nda")
      setActiveContractId(undefined)
      setActiveContractCreatedAt(undefined)
    }
  }, [selectedContract])

  const handleGenerate = async (data: typeof formData) => {
    setFormData(data)
    setIsGenerating(true)
    setError("")

    try {
      if (contractType === "custom-draft") {
        setContract(data.customDraft)
        setShowChat(true)
        persistContract(data.customDraft, data)
      } else {
        const generatedContract = await generateContractWithGemini(data, contractType)
        setContract(generatedContract)
        setShowChat(true)
        persistContract(generatedContract, data)
      }
    } catch (err) {
      setError("Failed to generate contract. Please try again.")
      console.error(err)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleContractUpdate = (updated: string) => {
    setContract(updated)
    persistContract(updated, formData)
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar Navigation */}
      <div className="w-64 bg-card border-r border-border flex flex-col">
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="w-5 h-5 text-primary" />
            <h1 className="text-xl font-bold text-foreground">ContractDraft</h1>
          </div>
          <p className="text-sm text-muted-foreground">AI-powered contract generation</p>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          <button
            onClick={() => handleContractTypeChange("nda")}
            className={`w-full text-left px-4 py-2 rounded-lg border transition-colors ${
              contractType === "nda" ? "bg-primary/10 border-primary" : "bg-transparent border-border hover:bg-accent"
            }`}
          >
            <div className="flex items-center gap-2 text-foreground font-medium">
              <Zap className="w-4 h-4" />
              NDA Template
            </div>
            <p className="text-xs text-muted-foreground mt-1">Non-Disclosure Agreement</p>
          </button>

          <button
            onClick={() => handleContractTypeChange("service-agreement")}
            className={`w-full text-left px-4 py-2 rounded-lg border transition-colors ${
              contractType === "service-agreement"
                ? "bg-primary/10 border-primary"
                : "bg-transparent border-border hover:bg-accent"
            }`}
          >
            <div className="flex items-center gap-2 text-foreground font-medium">
              <FileText className="w-4 h-4" />
              Service Agreement
            </div>
            <p className="text-xs text-muted-foreground mt-1">Contractor & Service Provider</p>
          </button>

          <button
            onClick={() => handleContractTypeChange("employment-offer")}
            className={`w-full text-left px-4 py-2 rounded-lg border transition-colors ${
              contractType === "employment-offer"
                ? "bg-primary/10 border-primary"
                : "bg-transparent border-border hover:bg-accent"
            }`}
          >
            <div className="flex items-center gap-2 text-foreground font-medium">
              <Briefcase className="w-4 h-4" />
              Offer Letter
            </div>
            <p className="text-xs text-muted-foreground mt-1">Employment Offer Letter</p>
          </button>

          <button
            onClick={() => handleContractTypeChange("custom-draft")}
            className={`w-full text-left px-4 py-2 rounded-lg border transition-colors ${
              contractType === "custom-draft"
                ? "bg-primary/10 border-primary"
                : "bg-transparent border-border hover:bg-accent"
            }`}
          >
            <div className="flex items-center gap-2 text-foreground font-medium">
              <Edit3 className="w-4 h-4" />
              Custom Draft
            </div>
            <p className="text-xs text-muted-foreground mt-1">Write or paste your own</p>
          </button>
        </nav>

        <div className="p-4 border-t border-border text-xs text-muted-foreground">
          <p>Powered by Google Gemini</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Form Panel */}
        <div className="w-1/2 overflow-y-auto border-r border-border bg-background">
          <ContractForm
            onGenerate={handleGenerate}
            isLoading={isGenerating}
            initialData={formData}
            error={error}
            contractType={contractType}
          />
        </div>

        {/* Preview & Chat Panel */}
        <div className="w-1/2 flex flex-col overflow-hidden">
          {showChat && contract ? (
            <>
              {/* Split between preview and chat */}
              <div className="flex-1 overflow-y-auto border-b border-border">
                <ContractPreview contract={contract} minimal />
              </div>
              <div className="flex-1 overflow-hidden">
                <ContractChat contract={contract} onContractUpdate={handleContractUpdate} contractType={contractType} />
              </div>
            </>
          ) : (
            <ContractPreview contract={contract} />
          )}

          {/* Export Actions */}
          {contract && (
            <div className="border-t border-border p-4 bg-background flex gap-2">
              <ExportMenu contract={contract} partyA={formData.partyA} partyB={formData.partyB} />
              <Button
                variant={showChat ? "default" : "outline"}
                className="flex-1"
                onClick={() => setShowChat(!showChat)}
              >
                <MessageCircle className="w-4 h-4 mr-2" />
                {showChat ? "Hide Chat" : "Refine"}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
