# Cogent Labs – Platform Infrastructure Engineer Assignment (Thumbnail API w/ Deployment)

We'd like to assess your technical skills by asking you to design, implement, and deploy a small API application that reflects the kind of work you might do if you joined Cogent Labs. The assignment is meant to cover a somewhat broad range of things, given the broad nature of the Platform Infrastructure Engineering team. You will be given **two weeks** to complete this challenge. Please read the instructions below carefully.

---

## 📘 Scenario

The engineers at Cogent Labs like to create custom emojis for their communication apps, which requires them to create many small thumbnail images.

Your job:
- Build a **long-running job API** that:
  - Accepts image files.
  - Creates 100x100 thumbnails.
  - Allows the thumbnails to be fetched after processing.

**Constraints**:
- The content of these emojis is **top secret**.
- Cogent wants to keep everything **on-premises**.
- You will not have direct access to the running systems or infrastructure.
- Your application must be **easily installable** by a Cogent engineer.
- If problems occur, Cogent should be able to easily:
  - Forward relevant information to you.
  - Or diagnose the issue themselves via your documentation.

---

## ✅ Requirementsz

You may enhance these features, but we don’t expect "bells and whistles". Focus on good judgment. Feel free to mention additional ideas in your README as future improvements.

### ✨ Functionality

1. **Image Submission**
   - POST an image to the API.
   - API saves the image and starts a long-running job to generate a 100x100 thumbnail.
   - Returns a **Job ID** for later status checks.

2. **Job Status**
   - GET job status via Job ID.
   - Status values: `"processing"`, `"succeeded"`, `"failed"`.

3. **Fetch Thumbnail**
   - Once the job has succeeded, allow fetching the thumbnail via API.

4. **List Jobs**
   - List all submitted jobs via API (in case a user forgets their Job ID).

> 🔒 No UI or authorization is needed—API only.

---

## 🏗 Architecture

Even though thumbnail generation is typically fast, your architecture **must support long-running jobs**, as more complex image processing may follow in the future.

---

## 🚀 Deployment & Operation

Cogent will:
- Use [kind](https://kind.sigs.k8s.io/) to create a **local Kubernetes cluster**.
- Load **locally built Docker images** into the cluster.

From your side:
- Docker images should be **easily buildable** with a **single command**.
- Helm chart(s) should be **easily deployable** to a **generic Kubernetes cluster** with a **single command**.

> 🛑 If this does not work out-of-the-box according to your instructions, your assignment will be rejected.

### 🧩 Debugging Support

Provide a way for users to extract **debugging information** in case of issues (assume users have full access to the cluster). This could include:
- Logging
- Metrics
- Monitoring

The choice is up to you.

---

## 🧪 Technologies

- Languages: **JavaScript**, **TypeScript**, or **Python**
- Use libraries/frameworks that **simplify development and testing**
- Must be:
  - **Packaged into Docker containers**
  - **Configured with Helm** for Kubernetes deployment

---

## 📄 Documentation (README)

Your README **must** include:

- ✅ How to install and use your application
- 🧠 Reasoning behind your technical and architectural choices
- ⚖️ Trade-offs you made, things left out, and what you'd do with more time
- 🏭 Discussion on what you’d do to fully **productionize** the system

---

## 📤 How to Submit

Send your submission to: **[engineering-assignment@cogent.co.jp](mailto:engineering-assignment@cogent.co.jp)**

Options:
- As an **unencrypted ZIP file** attachment
- Or a **link to a GitHub/Bitbucket repo**

📌 Be sure to include **your name** in both the email and the README.

---

## ✅ How It’s Reviewed

We evaluate your submission based on:

- ✅ Adherence to the requirements
- 🧹 Code/build/charts organization, readability, and style consistency
- 🧠 Quality of design decisions and future considerations
- 🔧 Approach to the challenges of **on-premises deployment and debugging**

> Submissions that do **not meet the minimum requirements** will be **rejected**.

If your submission passes, you'll be invited to an **extended technical interview**, where you will:

- Demo your working application
- Answer technical questions about it
- Implement and test some live changes