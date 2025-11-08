export interface SavedContract {
  id: string
  partyA: string
  partyB: string
  jurisdiction: string
  duration: string
  content: string
  createdAt: Date
  updatedAt: Date
}

const STORAGE_KEY = "contractdraft_contracts"

export function saveContract(contract: SavedContract) {
  const contracts = getAllContracts()
  const existing = contracts.findIndex((c) => c.id === contract.id)

  if (existing !== -1) {
    contracts[existing] = { ...contract, updatedAt: new Date() }
  } else {
    contracts.push({ ...contract, createdAt: new Date(), updatedAt: new Date() })
  }

  localStorage.setItem(STORAGE_KEY, JSON.stringify(contracts))
  return contract
}

export function getAllContracts(): SavedContract[] {
  if (typeof window === "undefined") return []
  const data = localStorage.getItem(STORAGE_KEY)
  return data ? JSON.parse(data) : []
}

export function getContract(id: string): SavedContract | undefined {
  return getAllContracts().find((c) => c.id === id)
}

export function deleteContract(id: string) {
  const contracts = getAllContracts()
  const filtered = contracts.filter((c) => c.id !== id)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
}
