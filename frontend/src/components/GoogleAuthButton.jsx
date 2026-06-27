import React from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { LogIn } from 'lucide-react';
import { authGoogle } from '../lib/api';

export default function GoogleAuthButton({ onAuthSuccess, onAuthError }) {
  const login = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const result = await authGoogle(tokenResponse.access_token);
        if (result.status === 'success') {
          onAuthSuccess(result.user);
        } else {
          onAuthError('Authentication failed');
        }
      } catch (err) {
        console.error(err);
        onAuthError('Google sign in failed');
      }
    },
    onError: (error) => {
      console.error('Google login error:', error);
      onAuthError(error);
    },
  });

  return (
    <button
      onClick={() => login()}
      className="flex items-center justify-center gap-2 w-full py-3 px-4 rounded-xl font-semibold text-white bg-farmGreen hover:bg-farmGreenDark transition-all duration-300 transform hover:scale-[1.02] shadow-lg shadow-green-500/20 active:scale-[0.98]"
    >
      <LogIn size={20} />
      <span>Login with Google</span>
    </button>
  );
}
