import { createEnv } from "@t3-oss/env-core";
import { z } from "zod";

export const env = createEnv({
  server: {
    POSTGRESQL_USERNAME: z.string(),
    POSTGRESQL_PASSWORD: z.string(),
    POSTGRESQL_DATABASE: z.string(),
    DB_HOST: z.string(),
    DB_PORT: z.coerce.number(),
    GEMINI_API_KEY: z.string(),
    DISCORD_TOKEN: z.string(),
    DISCORD_PUBLIC_KEY: z.string(),
    DISCORD_APPLICATION_ID: z.string(),
  },

  clientPrefix: "PUBLIC_",
  client: {},

  runtimeEnv: process.env,
  emptyStringAsUndefined: true,
});
