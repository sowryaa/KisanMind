import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { authGoogle } from '../lib/api';

export default function GoogleAuthButton({ onAuthSuccess, onAuthError }) {
  return (
    <GoogleLogin
      onSuccess={async (credentialResponse) => {
        try {
          const result = await authGoogle(credentialResponse.credential);
          if (result.status === 'success') {
            onAuthSuccess(result.user);
          } else {
            onAuthError('Authentication failed');
          }
        } catch (err) {
          console.error(err);
          onAuthError('Google sign in failed');
        }
      }}
      onError={() => onAuthError('Google sign in failed')}
    />
  );
}
