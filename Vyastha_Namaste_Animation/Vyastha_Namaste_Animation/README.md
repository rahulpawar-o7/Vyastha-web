# Vyastha Namaste Welcome Animation

Copy `WelcomeNamaste.jsx` and `WelcomeNamaste.css` into your Vyastha frontend.

Example:
import WelcomeNamaste from "./components/WelcomeNamaste";

<WelcomeNamaste
  userName={user?.name}
  onComplete={() => navigate("/dashboard")}
/>

The greeting is saved as `vyastha_greeting` in localStorage for this standalone version.
For production, save the greeting and animation preference in the Vyastha backend/database.
