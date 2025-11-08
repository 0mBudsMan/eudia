"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Zap, Loader2, AlertCircle } from "lucide-react"
import { CustomDraftEditor } from "@/components/custom-draft-editor"

interface ContractFormProps {
  onGenerate: (data: any) => void
  isLoading: boolean
  initialData: any
  error?: string
  contractType: string
}

export function ContractForm({ onGenerate, isLoading, initialData, error, contractType }: ContractFormProps) {
  const [formData, setFormData] = useState(initialData)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev: any) => ({ ...prev, [name]: value }))
  }

  const handleCustomDraftChange = (value: string) => {
    setFormData((prev: any) => ({ ...prev, customDraft: value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const isEmploymentOffer = contractType === "employment-offer"
    const isCustomDraft = contractType === "custom-draft"

    const requiredFields = isCustomDraft
      ? formData.customDraft?.trim()
      : isEmploymentOffer
        ? formData.companyName.trim() && formData.employeeName.trim() && formData.jobTitle.trim()
        : formData.partyA.trim() && formData.partyB.trim()

    if (!requiredFields) {
      return
    }
    onGenerate(formData)
  }

  const isNDA = contractType === "nda"
  const isServiceAgreement = contractType === "service-agreement"
  const isEmploymentOffer = contractType === "employment-offer"
  const isCustomDraft = contractType === "custom-draft"

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-foreground mb-2">
          {isNDA
            ? "Generate NDA"
            : isServiceAgreement
              ? "Generate Service Agreement"
              : isEmploymentOffer
                ? "Generate Employment Offer Letter"
                : "Custom Legal Draft"}
        </h2>
        <p className="text-muted-foreground">
          {isNDA
            ? "Fill in the details to generate a custom Non-Disclosure Agreement"
            : isServiceAgreement
              ? "Fill in the details to generate a custom Service Agreement / Independent Contractor Agreement"
              : isEmploymentOffer
                ? "Fill in the details to generate a professional Employment Offer Letter"
                : "Write or paste your own legal document and refine it with AI"}
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {isCustomDraft && (
          <Card className="p-6 border border-border">
            <h3 className="text-lg font-semibold text-foreground mb-4">Your Legal Document</h3>
            <CustomDraftEditor value={formData.customDraft || ""} onChange={handleCustomDraftChange} />
          </Card>
        )}

        {isEmploymentOffer && (
          <>
            <Card className="p-6 border border-border">
              <h3 className="text-lg font-semibold text-foreground mb-4">Company Information</h3>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="companyName" className="text-sm font-medium text-foreground">
                    Company Name
                  </Label>
                  <Input
                    id="companyName"
                    name="companyName"
                    value={formData.companyName || ""}
                    onChange={handleChange}
                    placeholder="e.g., Acme Corporation"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="companyAddress" className="text-sm font-medium text-foreground">
                    Company Address
                  </Label>
                  <Input
                    id="companyAddress"
                    name="companyAddress"
                    value={formData.companyAddress || ""}
                    onChange={handleChange}
                    placeholder="e.g., 123 Main St, San Francisco, CA"
                  />
                </div>
              </div>
            </Card>

            <Card className="p-6 border border-border">
              <h3 className="text-lg font-semibold text-foreground mb-4">Employee Information</h3>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="employeeName" className="text-sm font-medium text-foreground">
                    Employee Name
                  </Label>
                  <Input
                    id="employeeName"
                    name="employeeName"
                    value={formData.employeeName || ""}
                    onChange={handleChange}
                    placeholder="e.g., John Smith"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="employeeEmail" className="text-sm font-medium text-foreground">
                    Employee Email
                  </Label>
                  <Input
                    id="employeeEmail"
                    name="employeeEmail"
                    value={formData.employeeEmail || ""}
                    onChange={handleChange}
                    placeholder="e.g., john@example.com"
                    type="email"
                  />
                </div>
              </div>
            </Card>

            <Card className="p-6 border border-border">
              <h3 className="text-lg font-semibold text-foreground mb-4">Job Terms</h3>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="jobTitle" className="text-sm font-medium text-foreground">
                    Job Title
                  </Label>
                  <Input
                    id="jobTitle"
                    name="jobTitle"
                    value={formData.jobTitle || ""}
                    onChange={handleChange}
                    placeholder="e.g., Senior Software Engineer"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="department" className="text-sm font-medium text-foreground">
                    Department
                  </Label>
                  <Input
                    id="department"
                    name="department"
                    value={formData.department || ""}
                    onChange={handleChange}
                    placeholder="e.g., Engineering"
                  />
                </div>
                <div>
                  <Label htmlFor="salary" className="text-sm font-medium text-foreground">
                    Annual Salary
                  </Label>
                  <Input
                    id="salary"
                    name="salary"
                    value={formData.salary || ""}
                    onChange={handleChange}
                    placeholder="e.g., $150,000"
                  />
                </div>
                <div>
                  <Label htmlFor="startDate" className="text-sm font-medium text-foreground">
                    Start Date
                  </Label>
                  <Input
                    id="startDate"
                    name="startDate"
                    value={formData.startDate || ""}
                    onChange={handleChange}
                    placeholder="e.g., January 15, 2025"
                  />
                </div>
                <div>
                  <Label htmlFor="employmentType" className="text-sm font-medium text-foreground">
                    Employment Type
                  </Label>
                  <Input
                    id="employmentType"
                    name="employmentType"
                    value={formData.employmentType || ""}
                    onChange={handleChange}
                    placeholder="e.g., Full-time, Part-time"
                  />
                </div>
                <div>
                  <Label htmlFor="reportsTo" className="text-sm font-medium text-foreground">
                    Reports To
                  </Label>
                  <Input
                    id="reportsTo"
                    name="reportsTo"
                    value={formData.reportsTo || ""}
                    onChange={handleChange}
                    placeholder="e.g., Head of Engineering"
                  />
                </div>
                <div>
                  <Label htmlFor="benefits" className="text-sm font-medium text-foreground">
                    Benefits
                  </Label>
                  <Textarea
                    id="benefits"
                    name="benefits"
                    value={formData.benefits || ""}
                    onChange={handleChange}
                    placeholder="e.g., Health insurance, 401k, PTO, stock options"
                    rows={3}
                  />
                </div>
              </div>
            </Card>

            <Card className="p-6 border border-border">
              <h3 className="text-lg font-semibold text-foreground mb-4">Additional Details</h3>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="jurisdiction" className="text-sm font-medium text-foreground">
                    Jurisdiction
                  </Label>
                  <Input
                    id="jurisdiction"
                    name="jurisdiction"
                    value={formData.jurisdiction || ""}
                    onChange={handleChange}
                    placeholder="e.g., California"
                  />
                </div>
              </div>
            </Card>
          </>
        )}

        {(isNDA || isServiceAgreement) && (
          <Card className="p-6 border border-border">
            <h3 className="text-lg font-semibold text-foreground mb-4">Party Information</h3>

            <div className="space-y-4">
              <div>
                <Label htmlFor="partyA" className="text-sm font-medium text-foreground">
                  {isServiceAgreement ? "Company/Client Name" : "Your Company/Name"}
                </Label>
                <Input
                  id="partyA"
                  name="partyA"
                  value={formData.partyA}
                  onChange={handleChange}
                  placeholder={isServiceAgreement ? "e.g., ABC Corporation" : "e.g., Acme Corporation"}
                  required={!isEmploymentOffer}
                />
              </div>

              <div>
                <Label htmlFor="partyB" className="text-sm font-medium text-foreground">
                  {isServiceAgreement ? "Service Provider/Contractor Name" : "Other Party"}
                </Label>
                <Input
                  id="partyB"
                  name="partyB"
                  value={formData.partyB}
                  onChange={handleChange}
                  placeholder={isServiceAgreement ? "e.g., John Smith" : "e.g., Tech Innovations Inc."}
                  required={!isEmploymentOffer}
                />
              </div>
            </div>
          </Card>
        )}

        {(isNDA || isServiceAgreement) && (
          <Card className="p-6 border border-border">
            <h3 className="text-lg font-semibold text-foreground mb-4">Agreement Details</h3>

            <div className="space-y-4">
              {isServiceAgreement && (
                <>
                  <div>
                    <Label htmlFor="serviceScope" className="text-sm font-medium text-foreground">
                      Scope of Services
                    </Label>
                    <Textarea
                      id="serviceScope"
                      name="serviceScope"
                      value={formData.serviceScope || ""}
                      onChange={handleChange}
                      placeholder="Describe the services to be provided..."
                      rows={4}
                    />
                  </div>

                  <div>
                    <Label htmlFor="compensation" className="text-sm font-medium text-foreground">
                      Compensation / Rate
                    </Label>
                    <Input
                      id="compensation"
                      name="compensation"
                      value={formData.compensation || ""}
                      onChange={handleChange}
                      placeholder="e.g., $50/hour or $5,000 per project"
                    />
                  </div>

                  <div>
                    <Label htmlFor="paymentTerms" className="text-sm font-medium text-foreground">
                      Payment Terms
                    </Label>
                    <Input
                      id="paymentTerms"
                      name="paymentTerms"
                      value={formData.paymentTerms || ""}
                      onChange={handleChange}
                      placeholder="e.g., Net 30, Upon completion"
                    />
                  </div>
                </>
              )}

              {isNDA && (
                <>
                  <div>
                    <Label htmlFor="scope" className="text-sm font-medium text-foreground">
                      Scope of Confidential Information
                    </Label>
                    <Textarea
                      id="scope"
                      name="scope"
                      value={formData.scope}
                      onChange={handleChange}
                      placeholder="Describe what information should be considered confidential..."
                      rows={4}
                    />
                  </div>
                </>
              )}

              <div>
                <Label htmlFor="duration" className="text-sm font-medium text-foreground">
                  Agreement Duration
                </Label>
                <Input
                  id="duration"
                  name="duration"
                  value={formData.duration}
                  onChange={handleChange}
                  placeholder={isServiceAgreement ? "e.g., 6 months, 1 year" : "e.g., 2 years"}
                />
              </div>

              <div>
                <Label htmlFor="jurisdiction" className="text-sm font-medium text-foreground">
                  Jurisdiction
                </Label>
                <Input
                  id="jurisdiction"
                  name="jurisdiction"
                  value={formData.jurisdiction}
                  onChange={handleChange}
                  placeholder="e.g., California"
                />
              </div>
            </div>
          </Card>
        )}

        <div className="flex gap-3">
          <Button
            type="submit"
            disabled={
              isLoading ||
              (isCustomDraft
                ? !formData.customDraft?.trim()
                : isEmploymentOffer
                  ? !formData.companyName?.trim() || !formData.employeeName?.trim() || !formData.jobTitle?.trim()
                  : !formData.partyA?.trim() || !formData.partyB?.trim())
            }
            className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90"
            size="lg"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Loading...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 mr-2" />
                {isNDA
                  ? "Generate NDA"
                  : isServiceAgreement
                    ? "Generate Service Agreement"
                    : isEmploymentOffer
                      ? "Generate Offer Letter"
                      : "Load Document"}
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
