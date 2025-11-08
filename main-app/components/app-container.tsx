"use client"

import Link from "next/link"
import { useState } from "react"
import { ContractGenerator } from "./contract-generator"
import { Dashboard } from "./dashboard"
import { Button } from "@/components/ui/button"
import { Home, Plus } from "lucide-react"
import type { SavedContract } from "@/lib/contract-storage"

type View = "generator" | "dashboard"

export function AppContainer() {
  const [view, setView] = useState<View>("dashboard")
  const [selectedContract, setSelectedContract] = useState<SavedContract | undefined>()

  const handleSelectContract = (contract: SavedContract) => {
    setSelectedContract(contract)
    setView("generator")
  }

  const handleCreateNew = () => {
    setSelectedContract(undefined)
    setView("generator")
  }

  return (
    <>
      {/* Top Navigation */}
      <nav className="bg-card border-b border-border sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <Plus className="w-5 h-5 text-primary" />
            </div>
            <h1 className="text-xl font-bold text-foreground">ContractDraft</h1>
          </div>
          <div className="flex items-center gap-2">
            {view === "generator" && (
              <Button variant="ghost" onClick={() => setView("dashboard")}>
                <Home className="w-4 h-4 mr-2" />
                Dashboard
              </Button>
            )}
            <Button asChild variant="outline" className="hidden sm:flex">
              <Link href="/">Case Analyzer</Link>
            </Button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      {view === "dashboard" ? (
        <Dashboard onSelectContract={handleSelectContract} onCreateNew={handleCreateNew} />
      ) : (
        <ContractGenerator selectedContract={selectedContract} />
      )}
    </>
  )
}
