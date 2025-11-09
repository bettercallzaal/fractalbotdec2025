import NextAuth from 'next-auth';
import DiscordProvider from 'next-auth/providers/discord';
import { db } from '../../../utils/database';
import { users } from '../../../utils/schema';
import { eq } from 'drizzle-orm';

export default NextAuth({
  providers: [
    DiscordProvider({
      clientId: process.env.DISCORD_CLIENT_ID!,
      clientSecret: process.env.DISCORD_CLIENT_SECRET!,
      authorization: {
        params: {
          scope: 'identify email guilds',
        },
      },
    }),
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      if (account?.provider === 'discord' && profile) {
        try {
          // Check if user exists in database
          const existingUser = await db
            .select()
            .from(users)
            .where(eq(users.discordId, String(profile.id)))
            .limit(1);

          if (existingUser.length === 0) {
            // Create new user
            await db.insert(users).values({
              discordId: String(profile.id),
              username: String(profile.username),
              displayName: String(profile.global_name || profile.username),
              avatarUrl: `https://cdn.discordapp.com/avatars/${profile.id}/${profile.avatar}.png`,
            });
          } else {
            // Update existing user info
            await db
              .update(users)
              .set({
                username: String(profile.username),
                displayName: String(profile.global_name || profile.username),
                avatarUrl: `https://cdn.discordapp.com/avatars/${profile.id}/${profile.avatar}.png`,
                updatedAt: new Date(),
              })
              .where(eq(users.discordId, String(profile.id)));
          }
        } catch (error) {
          console.error('Error handling user sign in:', error);
          return false;
        }
      }
      return true;
    },
    async session({ session, token }) {
      if (token.sub) {
        // Get user data from database
        const userData = await db
          .select()
          .from(users)
          .where(eq(users.discordId, String(token.sub)))
          .limit(1);

        if (userData.length > 0) {
          session.user.id = userData[0].id.toString();
          session.user.discordId = userData[0].discordId;
          session.user.walletAddress = userData[0].walletAddress;
          session.user.totalFractals = userData[0].totalFractals;
          session.user.totalWins = userData[0].totalWins;
        }
      }
      return session;
    },
    async jwt({ token, account, profile }) {
      if (account && profile) {
        token.discordId = profile.id;
      }
      return token;
    },
  },
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  session: {
    strategy: 'jwt',
  },
});
