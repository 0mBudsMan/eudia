export async function generateContractWithGemini(
  formData: {
    partyA: string
    partyB: string
    duration: string
    scope?: string
    serviceScope?: string
    compensation?: string
    paymentTerms?: string
    jurisdiction: string
    restrictions?: string[]
  },
  contractType = "nda",
) {
  try {
    const response = await fetch("/api/generate-contract", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...formData, contractType }),
    })

    if (!response.ok) {
      throw new Error("Failed to generate contract")
    }

    const data = await response.json()
    return data.contract
  } catch (error) {
    console.error("Error in generateContractWithGemini:", error)
    throw error
  }
}

export async function refineContractWithGemini(contract: string, instruction: string) {
  try {
    const prompt = `Here is a contract that needs refinement:

${contract}

User instruction for refinement: ${instruction}

Please apply this refinement to the contract while maintaining its legal structure and completeness. Return only the refined contract.`

    const response = await fetch("/api/refine-contract", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    })

    if (!response.ok) {
      throw new Error("Failed to refine contract")
    }

    const data = await response.json()
    return data.contract
  } catch (error) {
    console.error("Error in refineContractWithGemini:", error)
    throw error
  }
}
