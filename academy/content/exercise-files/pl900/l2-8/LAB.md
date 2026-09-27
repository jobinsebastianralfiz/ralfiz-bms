# PL-900 · 2.8 Privacy, accessibility and data policies

## Files
- dlp-policy-spec.md

## Steps
1. Download dlp-policy-spec.md.
2. In the admin center, open Policies > Data policies and create "Help Desk DLP" scoped only to your developer environment.
3. Move Microsoft Dataverse and Office 365 Outlook to Business and a social media connector to Blocked. Save the policy.
4. Wait a few minutes, then build test 1 from the spec in Power Automate and copy the error text into the file.
5. Build tests 2 and 3 and record the results.
6. Delete the test flows.
7. After Lesson 3.1, open your canvas app, run App checker > Accessibility and work through the accessibility checklist.

## Check your work
- [ ] Help Desk DLP appears in Data policies with your developer environment as its only scope.
- [ ] Test 1: the flow with the blocked connector cannot be saved or turned on, and the message mentions a data policy.
- [ ] Test 2: Dataverse (Business) and RSS (Non-business) cannot be used together in one flow.
- [ ] Test 3: Dataverse with Office 365 Outlook saves and runs.
