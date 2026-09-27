// src/telemetry.ts - forward code app platform metrics to Application Insights.
// npm install @microsoft/applicationinsights-web
// Call initTelemetry() once in src/main.tsx before rendering the app.
import { ApplicationInsights } from "@microsoft/applicationinsights-web";
import { setConfig, getContext } from "@microsoft/power-apps/app";

// Environment variables are not supported for this key. Pick the connection string per environment
// (or read it from a Dataverse settings table). Replace the IDs and strings with your own.
const CONNECTION_STRINGS: Record<string, string> = {
  "DEV-ENVIRONMENT-ID": "InstrumentationKey=00000000-0000-0000-0000-000000000000;IngestionEndpoint=https://westeurope-5.in.applicationinsights.azure.com/",
  "TEST-ENVIRONMENT-ID": "InstrumentationKey=11111111-1111-1111-1111-111111111111;IngestionEndpoint=https://westeurope-5.in.applicationinsights.azure.com/"
};

let appInsights: ApplicationInsights | null = null;

export async function initTelemetry(): Promise<void> {
  const ctx = await getContext();
  const connectionString = CONNECTION_STRINGS[ctx.app.environmentId];
  if (!connectionString) {
    console.warn("No Application Insights connection string for environment " + ctx.app.environmentId);
    return;
  }

  appInsights = new ApplicationInsights({ config: { connectionString: connectionString } });
  appInsights.loadAppInsights();

  setConfig({
    logger: {
      // value.type is "sessionLoadSummary" or "networkRequest"; value.data holds the measurements.
      logMetric: (value) => {
        appInsights?.trackEvent({ name: value.type }, value.data);
      }
    }
  });
}
