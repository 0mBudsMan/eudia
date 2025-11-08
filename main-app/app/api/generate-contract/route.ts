import { GoogleGenerativeAI } from "@google/generative-ai"
import { type NextRequest, NextResponse } from "next/server"

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!)

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { partyA, partyB, duration, scope, serviceScope, compensation, paymentTerms, jurisdiction, contractType } =
      body

    let prompt = ""

    if (contractType === "employment-offer") {
      const {
        companyName,
        companyAddress,
        employeeName,
        employeeEmail,
        jobTitle,
        department,
        salary,
        startDate,
        employmentType,
        reportsTo,
        benefits,
      } = body

      prompt = `Generate a professional Employment Offer Letter with the following details:

Company Name: ${companyName}
Company Address: ${companyAddress}
Employee Name: ${employeeName}
Employee Email: ${employeeEmail}
Position: ${jobTitle}
Department: ${department}
Start Date: ${startDate}
Employment Type: ${employmentType}
Annual Salary: ${salary}
Reports To: ${reportsTo}
Benefits: ${benefits}
Jurisdiction: ${jurisdiction}

Create a complete, professional Employment Offer Letter that includes:
1. Header with company name and address
2. Date of offer
3. Greeting to the employee
4. Introduction and position details
5. Job title and department
6. Start date and employment type
7. Compensation and benefits
8. Reporting structure
9. At-will employment statement
10. Conditions of employment
11. Confidentiality and IP agreement reference
12. Signature lines for both company and employee
13. At-will employment disclaimer

Format it as a formal business letter with proper spacing and professional tone. Make it complete and ready to use.`
    } else if (contractType === "service-agreement") {
      prompt = `Generate a professional Service Agreement / Independent Contractor Agreement with the following details:

Service Provider/Contractor: ${partyB}
Client/Company: ${partyA}
Scope of Services: ${serviceScope}
Compensation: ${compensation}
Payment Terms: ${paymentTerms}
Agreement Duration: ${duration}
Jurisdiction: ${jurisdiction}

Create a complete, legally-structured Service Agreement that includes:
1. Definitions (Independent Contractor, Services, Deliverables)
2. Scope of Services
3. Compensation and Payment Terms
4. Term and Termination
5. Confidentiality and Non-Disclosure
6. Intellectual Property Rights
7. Liability and Indemnification
8. Independent Contractor Status
9. Governing Law and Jurisdiction
10. Entire Agreement and Amendments
11. Signatures

Format it as a formal legal document with proper sections and numbering. Make it comprehensive and professional.`
    } else {
      prompt = `Generate a professional Non-Disclosure Agreement (NDA) with the following details:

Party A (Disclosing Party): ${partyA}
Party B (Receiving Party): ${partyB}
Agreement Duration: ${duration}
Jurisdiction: ${jurisdiction}
Scope of Confidential Information: ${scope}

Create a complete, legally-structured NDA that includes:
1. Definitions (Confidential Information, Purpose, Disclosure)
2. Obligations of Receiving Party
3. Exclusions from Confidentiality
4. Return of Information
5. Term and Termination
6. Remedies
7. Governing Law and Jurisdiction
8. Severability
9. Entire Agreement
10. Signatures

Format it as a formal legal document with proper sections and numbering. Make it comprehensive but adaptable.`
    }

    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" })

    const result = await model.generateContent(prompt)
    const generatedText = result.response.text()

    return NextResponse.json({ contract: generatedText })
  } catch (error) {
    console.error("Error generating contract:", error)
    return NextResponse.json({ error: "Failed to generate contract" }, { status: 500 })
  }
}
