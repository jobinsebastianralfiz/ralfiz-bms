// ESLint 9 flat config. Install first:
//   npm install --save-dev eslint @eslint/js globals
// Then run: npx eslint .
import js from '@eslint/js';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: globals.node,
    },
    rules: {
      eqeqeq: 'error',
      'prefer-const': 'warn',
    },
  },
];
