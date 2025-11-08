import { Card } from "@/components/ui/card"
import { FileText } from "lucide-react"

interface ContractPreviewProps {
  contract: string
  minimal?: boolean
}

export function ContractPreview({ contract, minimal = false }: ContractPreviewProps) {
  return (
    <div className={minimal ? "h-full flex flex-col" : "p-8"}>
      {!minimal && (
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-foreground mb-2">Document Preview</h2>
          <p className="text-muted-foreground text-sm">Your generated NDA will appear here</p>
        </div>
      )}

      {contract ? (
        <Card
          className={`${minimal ? "flex-1 m-4 mb-0" : ""} p-6 bg-background border border-border font-serif overflow-y-auto`}
        >
          <div className="prose prose-invert max-w-none text-foreground whitespace-pre-wrap text-sm leading-relaxed">
            {contract}
          </div>
        </Card>
      ) : (
        <Card
          className={`${minimal ? "" : "p-12"} bg-background/50 border-2 border-dashed border-border ${minimal ? "m-4 flex items-center justify-center" : "flex flex-col items-center justify-center min-h-96"}`}
        >
          <FileText className="w-12 h-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground text-center">
            Fill in the form and click "Generate NDA" to preview your contract
          </p>
        </Card>
      )}
    </div>
  )
}
