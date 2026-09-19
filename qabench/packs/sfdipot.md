# SFDIPOT — Bach's Heuristic Test Strategy Model; the seven questions to ask of any surface before saying it works
STRUCTURE — what is it made of: the screen, the components under it, the two layers that must agree (what the server serves, what the client reads; what the printer draws, what the scanner decodes).
FUNCTION — what does it do: every control on the surface, every verb it offers, the verbs the API has that the surface does NOT offer, a control offered twice, a screen that can add and cannot remove.
DATA — what does it process: the shapes above, and the shapes THIS system's data never held.
INTERFACES — how it is reached: the menu, a row button, a URL pasted from a colleague, a deep link from a notification, the browser's back and reload.
PLATFORM — what it depends on: the second browser engine (WebKit is not Chromium: no BarcodeDetector, popups refused after an await, pinch-zoom parts the two viewports) · the phone's width AND height with the keyboard open · the printer's paper size AND orientation · the scanner's symbology · the camera's whole field of view, not the code it was aimed at.
OPERATIONS — how it is used: as the least privileged role, as a customer-scoped account, on the warehouse floor with one hand, mid-shift when the mirror refreshes.
TIME — when: after a deploy under an open tab · at session expiry · on the day the decision that shaped it stopped being true.
