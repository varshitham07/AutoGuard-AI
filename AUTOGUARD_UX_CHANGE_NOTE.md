# AutoGuard AI — UX and Design Change Note

Date: 22 November 2026

## Product direction
AutoGuard AI should feel like a professionally designed automotive fleet and vehicle-care product, not a generic AI dashboard or a set of disconnected generated cards. The interface follows familiar fleet-management software patterns: persistent workspace navigation, clear page hierarchy, concise status indicators, structured records, and task-oriented actions.

## Design requirements
- Use a restrained automotive visual identity: deep navy, white, neutral surfaces, and meaningful status colors.
- Keep typography, spacing, button styles, form controls, tables, and status labels consistent across all sections.
- Use automotive imagery as context, not decoration that competes with the actual work.
- Make the interface easy to understand for a first-time user; use clear labels instead of unexplained technical terms.
- Keep the layout responsive and usable on desktop and mobile.
- Provide visible keyboard focus, reduced-motion support, and clear active-navigation state.
- Avoid excessive animation, overly rounded generic cards, crowded pages, and repeated style overrides.

## Navigation and user journey
Primary workflow:
1. Register a vehicle and enter its odometer.
2. Record a condition or tyre check.
3. Create a maintenance work order when follow-up is needed.
4. Update the service history after work is completed.
5. Review vehicle health reports and fleet insights.

Related pages should provide a contextual previous/next action so users can move through the workflow without returning to the navigation menu each time.

## Changes implemented in the current UX pass
- Reordered the navigation to place Vehicles, Maintenance, and Alerts under Fleet Operations.
- Kept diagnostics, records/reporting, and workshop support grouped by purpose.
- Added a contextual workflow footer to all 14 main sections with a relevant next action and a return/previous action.
- Added a global Register vehicle action in the top bar.
- Improved page switching: validates the target section, updates active navigation and the page title, moves focus to the main content, and scrolls to the top.
- Added keyboard-focus styling and reduced-motion handling.
- Reduced unnecessary card and logo animation for a calmer professional interface.
- Preserved the existing feature sections and data workflows; no new backend capability is claimed by this design update.
- Kept root `index.html` and `web/index.html` synchronized.

## Functionality and honesty
- Fleet records and maintenance actions depend on the configured backend or local demo mode.
- Tyre condition screening is rule-based and uses user-entered readings.
- Scania APS prediction is dataset-specific and requires a trained model installed on the backend.
- Tyre photo notes are visual previews, not automated diagnosis.
- Mechanic discovery opens an external map search; it is not a verified booking system.
- This prototype does not certify vehicle roadworthiness and does not connect to live OBD/CAN sensors.

## QA checklist before calling the redesign complete
- Verify sign-in and account creation in backend mode.
- Register a vehicle and confirm it appears in the fleet register.
- Run a tyre/condition check and create a work order from the finding.
- Update a work order and record completed service.
- Confirm reports, reminders, and insights load from actual stored data.
- Check all contextual workflow buttons and navigation on desktop and mobile.
- Confirm GitHub Pages deployment succeeds and inspect the live page at mobile width.


# AutoGuard AI — usability and button fixes

## User feedback
The user reported that buttons were not working and the website felt difficult to access.

## Changes made
- Added an **Explore demo workspace** entry on GitHub Pages so users can open the browser demo without first creating an account.
- The demo entry creates a local demo operator only when needed, preserves existing browser demo data, and loads clearly labelled sample records if the workspace is empty.
- Clarified that browser demo records remain on the current device and are not secure multi-user account data.
- Kept backend-hosted sign-in/register separate from the static GitHub Pages demo.
- Explicitly set button types where missing to avoid accidental form submission.
- Increased button/navigation tap targets and improved visible keyboard focus.
- Kept mobile workflow actions readable and easier to tap.

## Test status
- JavaScript syntax check is required after deployment.
- Test the demo entry, page navigation, form submission, sample-data loader, and mobile menu in the published site.
- This is a usability fix; it does not turn the prototype into a certified vehicle diagnostic or live telemetry system.


## Final interaction and responsive repair (22 Nov 2026)
- Fixed navigation loops that used `querySelector()` as though it returned a collection. Navigation now iterates with `querySelectorAll()`, allowing page links and section changes to run.
- Corrected button semantics: all action buttons default to `type="button"`; only each form's primary action is set to `type="submit"`. This prevents secondary buttons (such as demo exploration or refresh actions) from accidentally submitting a form.
- Added a final responsive pass for the mobile menu, stacked content, touch-sized controls, full-width form fields, and horizontally scrollable data tables without forcing the whole page off-screen.
- No new product features or model claims were added.
