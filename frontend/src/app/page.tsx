import { redirect } from "next/navigation";

/** Root route sends the investigator straight to the dashboard. */
export default function Home() {
  redirect("/dashboard");
}
