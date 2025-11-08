"use client"

import { useState, useEffect, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { FileText, Plus, MoreVertical, Trash2, Edit, Download, Search, Filter, Calendar, Building2 } from "lucide-react"
import { getAllContracts, deleteContract, type SavedContract } from "@/lib/contract-storage"

interface DashboardProps {
  onSelectContract?: (contract: SavedContract) => void
  onCreateNew?: () => void
}

export function Dashboard({ onSelectContract, onCreateNew }: DashboardProps) {
  const [contracts, setContracts] = useState<SavedContract[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [sortBy, setSortBy] = useState<"recent" | "oldest" | "name">("recent")
  const [filterJurisdiction, setFilterJurisdiction] = useState<string | null>(null)

  useEffect(() => {
    const saved = getAllContracts()
    setContracts(saved)
  }, [])

  const jurisdictions = useMemo(() => {
    const unique = new Set(contracts.map((c) => c.jurisdiction))
    return Array.from(unique).sort()
  }, [contracts])

  const filteredAndSorted = useMemo(() => {
    let filtered = contracts

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(
        (c) =>
          c.partyA.toLowerCase().includes(query) ||
          c.partyB.toLowerCase().includes(query) ||
          c.duration.toLowerCase().includes(query),
      )
    }

    // Filter by jurisdiction
    if (filterJurisdiction) {
      filtered = filtered.filter((c) => c.jurisdiction === filterJurisdiction)
    }

    // Sort
    const sorted = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case "recent":
          return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
        case "oldest":
          return new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime()
        case "name":
          return `${a.partyA}${a.partyB}`.localeCompare(`${b.partyA}${b.partyB}`)
        default:
          return 0
      }
    })

    return sorted
  }, [contracts, searchQuery, sortBy, filterJurisdiction])

  const stats = useMemo(() => {
    return {
      total: contracts.length,
      jurisdictions: jurisdictions.length,
    }
  }, [contracts, jurisdictions])

  const handleDelete = (id: string) => {
    deleteContract(id)
    setContracts((prev) => prev.filter((c) => c.id !== id))
  }

  const handleSelectContract = (contract: SavedContract) => {
    onSelectContract?.(contract)
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto p-6 md:p-8">
        {/* Header Section */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">Contract Manager</h1>
          <p className="text-muted-foreground">Manage, organize, and track all your NDAs in one place</p>
        </div>

        {/* Statistics Cards */}
        {contracts.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <Card className="bg-card/50 border-border/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Total Contracts</p>
                    <p className="text-3xl font-bold text-foreground">{stats.total}</p>
                  </div>
                  <FileText className="w-8 h-8 text-primary/40" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-card/50 border-border/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Jurisdictions</p>
                    <p className="text-3xl font-bold text-foreground">{stats.jurisdictions}</p>
                  </div>
                  <Building2 className="w-8 h-8 text-primary/40" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Action Bar */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <Button onClick={onCreateNew} className="bg-primary text-primary-foreground hover:bg-primary/90" size="lg">
            <Plus className="w-4 h-4 mr-2" />
            Create New NDA
          </Button>

          {/* Search Bar */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by party name or duration..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-input border border-border rounded-md text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          {/* Filter and Sort Controls */}
          {jurisdictions.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2 bg-transparent">
                  <Filter className="w-4 h-4" />
                  Jurisdiction
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem
                  onClick={() => setFilterJurisdiction(null)}
                  className={filterJurisdiction === null ? "bg-accent" : ""}
                >
                  All Jurisdictions
                </DropdownMenuItem>
                {jurisdictions.map((j) => (
                  <DropdownMenuItem
                    key={j}
                    onClick={() => setFilterJurisdiction(j)}
                    className={filterJurisdiction === j ? "bg-accent" : ""}
                  >
                    {j}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="gap-2 bg-transparent">
                <Calendar className="w-4 h-4" />
                Sort
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuItem onClick={() => setSortBy("recent")} className={sortBy === "recent" ? "bg-accent" : ""}>
                Most Recent
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy("oldest")} className={sortBy === "oldest" ? "bg-accent" : ""}>
                Oldest First
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy("name")} className={sortBy === "name" ? "bg-accent" : ""}>
                Party Name
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Contracts Grid */}
        {filteredAndSorted.length === 0 ? (
          <Card className="p-12 text-center border-2 border-dashed border-border">
            <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">
              {contracts.length === 0 ? "No Contracts Yet" : "No Results Found"}
            </h3>
            <p className="text-muted-foreground mb-6">
              {contracts.length === 0 ? "Create your first NDA to get started" : "Try adjusting your search or filters"}
            </p>
            {contracts.length === 0 && (
              <Button onClick={onCreateNew} className="bg-primary text-primary-foreground hover:bg-primary/90">
                <Plus className="w-4 h-4 mr-2" />
                Create NDA
              </Button>
            )}
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredAndSorted.map((contract) => (
              <Card
                key={contract.id}
                className="p-6 cursor-pointer hover:border-primary transition-all duration-200 border border-border hover:bg-card/80 hover:shadow-lg"
                onClick={() => handleSelectContract(contract)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <FileText className="w-5 h-5 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <h3 className="font-semibold text-foreground truncate">NDA</h3>
                      <p className="text-sm text-muted-foreground truncate">
                        {contract.partyA} & {contract.partyB}
                      </p>
                    </div>
                  </div>

                  {/* More Menu */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                      <Button variant="ghost" size="icon" className="flex-shrink-0 ml-2">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation()
                          handleSelectContract(contract)
                        }}
                      >
                        <Edit className="w-4 h-4 mr-2" />
                        Open
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation()
                          const text = contract.content
                          const blob = new Blob([text], { type: "text/plain" })
                          const url = URL.createObjectURL(blob)
                          const link = document.createElement("a")
                          link.href = url
                          link.download = `NDA-${contract.partyA}-${contract.id}.txt`
                          link.click()
                        }}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(contract.id)
                        }}
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                {/* Contract Meta */}
                <div className="space-y-2 text-sm border-t border-border pt-4">
                  <div className="flex justify-between text-muted-foreground">
                    <span>Duration:</span>
                    <span className="font-medium text-foreground">{contract.duration}</span>
                  </div>
                  <div className="flex justify-between text-muted-foreground">
                    <span>Jurisdiction:</span>
                    <span className="font-medium text-foreground">{contract.jurisdiction}</span>
                  </div>
                  <div className="pt-2 border-t border-border text-xs text-muted-foreground">
                    Updated {new Date(contract.updatedAt).toLocaleDateString()}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
