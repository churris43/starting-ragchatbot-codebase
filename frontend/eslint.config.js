export default [
  {
    files: ['**/*.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        // Browser globals
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        fetch: 'readonly',
        Date: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        // External libraries loaded via CDN
        marked: 'readonly',
      },
    },
    rules: {
      // Possible errors
      'no-console': 'off',
      'no-debugger': 'warn',
      'no-duplicate-case': 'error',
      'no-empty': 'warn',
      'no-extra-semi': 'error',
      'no-func-assign': 'error',
      'no-irregular-whitespace': 'error',
      'no-unreachable': 'error',
      'no-unsafe-negation': 'error',
      'valid-typeof': 'error',

      // Best practices
      curly: ['error', 'multi-line'],
      eqeqeq: ['error', 'always', { null: 'ignore' }],
      'no-empty-function': 'warn',
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-multi-spaces': 'error',
      'no-new-wrappers': 'error',
      'no-return-assign': 'error',
      'no-self-assign': 'error',
      'no-unused-expressions': 'error',
      'no-useless-return': 'error',

      // Variables
      'no-shadow': 'warn',
      'no-undef': 'error',
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-use-before-define': ['error', { functions: false }],

      // Stylistic (let Prettier handle most formatting)
      'no-trailing-spaces': 'error',
      'no-multiple-empty-lines': ['error', { max: 2, maxEOF: 1 }],
    },
  },
  {
    ignores: ['node_modules/', 'dist/', 'build/', 'coverage/'],
  },
];
