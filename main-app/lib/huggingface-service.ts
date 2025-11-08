let appPromise: Promise<any> | null = null

export async function ensureGradioClient() {
  if (!appPromise) {
    const { Client } = await import("@gradio/client")
    appPromise = Client.connect("aarohanverma/lstm-next-word-predictor-demo")
  }
  return appPromise
}

export async function getNextWordPrediction(text: string): Promise<string[]> {
  try {
    const app = await ensureGradioClient()

    console.log("[v0] Connected to Gradio app")

    // Try the most common endpoint names for Gradio
    const endpoints = ["/submit_and_predict", "/append_suggestion"]

    for (const endpoint of endpoints) {
      try {
        console.log("[v0] Trying endpoint:", endpoint)
        const result = await app.predict(endpoint, [text])

        console.log("[v0] Got result from endpoint", endpoint, ":", result)

        // The API returns: { data: [{ value: "word1" }, { value: "word2" }, { value: "word3" }] }
        const predictions = result?.data || []
        const extractedPredictions = predictions
          .map((item: any) => {
            // Handle both object format { value: "..." } and string format
            return typeof item === "object" && item?.value ? item.value : item
          })
          .filter((word: string) => word && typeof word === "string")
          .map((word: string) => word.trim())

        console.log("[v0] Extracted predictions:", extractedPredictions)

        if (extractedPredictions.length > 0) {
          return extractedPredictions
        }
      } catch (endpointError) {
        console.log("[v0] Endpoint", endpoint, "failed:", endpointError)
        continue
      }
    }

    console.log("[v0] All endpoints failed")
    return []
  } catch (error) {
    console.log("[v0] Error getting prediction:", error)
    return []
  }
}
