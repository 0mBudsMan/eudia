import { GoogleGenerativeAI } from "@google/generative-ai"
import { type NextRequest, NextResponse } from "next/server"

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!)

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { prompt } = body

    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" })

    const result = await model.generateContent(prompt)
    const generatedText = result.response.text()

    return NextResponse.json({ contract: generatedText })
  } catch (error) {
    console.error("Error refining contract:", error)
    return NextResponse.json({ error: "Failed to refine contract" }, { status: 500 })
  }
}
