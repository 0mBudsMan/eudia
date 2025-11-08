"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import { Download, FileText, File, Printer, Copy, Check } from "lucide-react"
import { exportAsText, exportAsPDF, printContract } from "@/lib/export-service"

interface ExportMenuProps {
  contract: string
  partyA: string
  partyB: string
}

export function ExportMenu({ contract, partyA, partyB }: ExportMenuProps) {
  const [copied, setCopied] = useState(false)

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(contract)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handlePDFExport = async () => {
    try {
      await exportAsPDF(contract, partyA, partyB)
    } catch (error) {
      console.error("PDF export failed:", error)
      alert("Failed to export as PDF. Please try again.")
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="bg-transparent">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuItem onClick={() => exportAsText(contract, partyA, partyB)}>
          <FileText className="w-4 h-4 mr-2" />
          Download as TXT
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handlePDFExport}>
          <File className="w-4 h-4 mr-2" />
          Download as PDF
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => printContract(contract)}>
          <Printer className="w-4 h-4 mr-2" />
          Print
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleCopyToClipboard}>
          {copied ? (
            <>
              <Check className="w-4 h-4 mr-2" />
              Copied!
            </>
          ) : (
            <>
              <Copy className="w-4 h-4 mr-2" />
              Copy to Clipboard
            </>
          )}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
