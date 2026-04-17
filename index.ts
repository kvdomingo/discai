import { createDiscordAdapter } from "@chat-adapter/discord";
import { createPostgresState } from "@chat-adapter/state-pg";
import { Chat } from "chat";
import { env } from "./env";

export const bot = new Chat({
  userName: "discai",
  adapters: {
    discord: createDiscordAdapter({
      botToken: env.DISCORD_TOKEN,
      publicKey: env.DISCORD_PUBLIC_KEY,
      applicationId: env.DISCORD_APPLICATION_ID,
    }),
  },
  state: createPostgresState({
    url: `postgres://${env.POSTGRESQL_USERNAME}:${env.POSTGRESQL_PASSWORD}@${env.DB_HOST}:${env.DB_PORT}/${env.POSTGRESQL_DATABASE}`,
  }),
  streamingUpdateIntervalMs: 1000,
});

bot.onNewMention(async (thread) => {
  await thread.subscribe();
  await thread.post("Hello! I'm listening to this thread.");
});
