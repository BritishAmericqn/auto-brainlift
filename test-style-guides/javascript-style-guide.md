# JavaScript/TypeScript Style Guide

## Table of Contents
1. [Naming Conventions](#naming-conventions)
2. [Code Formatting](#code-formatting)
3. [Best Practices](#best-practices)
4. [Error Handling](#error-handling)
5. [Documentation](#documentation)
6. [Testing](#testing)

## Naming Conventions

### Variables and Functions
- Use camelCase for variable and function names
- Use descriptive names that explain the purpose
- Prefer const over let, avoid var
- Boolean variables should start with is, has, or should

```javascript
// Good
const isLoading = true;
const hasPermission = checkUserPermissions();
const shouldRefresh = false;

// Bad
const loading = true;
const permission = checkUserPermissions();
const refresh = false;
```

### Classes and Interfaces
- Use PascalCase for class names and interfaces
- Interface names should NOT be prefixed with 'I'
- Use descriptive names that indicate the purpose

```typescript
// Good
class UserController { }
interface UserData { }

// Bad
class userController { }
interface IUserData { }
```

### Constants
- Use UPPER_SNAKE_CASE for true constants
- Group related constants in objects

```javascript
// Good
const MAX_RETRY_ATTEMPTS = 3;
const API_ENDPOINTS = {
  USERS: '/api/users',
  POSTS: '/api/posts',
};

// Bad
const maxRetryAttempts = 3;
const users_endpoint = '/api/users';
```

## Code Formatting

### Indentation and Spacing
- Use 2 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Add space around operators
- No trailing whitespace

### Quotes
- Use single quotes for strings
- Use template literals for string interpolation
- Use double quotes for JSX attributes

```javascript
// Good
const message = 'Hello World';
const greeting = `Hello ${name}`;
<Component prop="value" />

// Bad
const message = "Hello World";
const greeting = 'Hello ' + name;
```

### Semicolons
- Always use semicolons
- Don't rely on ASI (Automatic Semicolon Insertion)

### Functions
- Use arrow functions for callbacks
- Use function declarations for top-level functions
- Always use parentheses for arrow function parameters

```javascript
// Good
function processData(data) {
  return data.map(item => item.value);
}

const handler = (event) => {
  console.log(event);
};

// Bad
const processData = (data) => {
  return data.map(item => item.value);
}

const handler = event => console.log(event);
```

## Best Practices

### Async/Await
- Prefer async/await over promises
- Always handle errors with try/catch
- Use Promise.all for parallel operations

```javascript
// Good
async function fetchUserData(userId) {
  try {
    const user = await api.getUser(userId);
    const posts = await api.getUserPosts(userId);
    return { user, posts };
  } catch (error) {
    logger.error('Failed to fetch user data', error);
    throw new Error('User data fetch failed');
  }
}

// Bad
function fetchUserData(userId) {
  return api.getUser(userId)
    .then(user => {
      return api.getUserPosts(userId)
        .then(posts => ({ user, posts }));
    })
    .catch(error => {
      console.log(error);
    });
}
```

### Object and Array Destructuring
- Use destructuring to extract values
- Provide default values when appropriate
- Use rest parameters for flexible functions

```javascript
// Good
const { name, age = 18 } = user;
const [first, second, ...rest] = array;

function processOptions({ timeout = 5000, retries = 3 } = {}) {
  // ...
}

// Bad
const name = user.name;
const age = user.age || 18;
```

### Immutability
- Avoid mutating objects and arrays
- Use spread operator for shallow copies
- Use Array methods that return new arrays

```javascript
// Good
const newUser = { ...user, name: 'New Name' };
const newArray = [...array, newItem];
const filtered = array.filter(item => item.active);

// Bad
user.name = 'New Name';
array.push(newItem);
```

## Error Handling

### Try-Catch Blocks
- Always catch and handle errors appropriately
- Log errors with context
- Throw custom errors with meaningful messages

```javascript
// Good
try {
  const result = await riskyOperation();
  return processResult(result);
} catch (error) {
  logger.error('Risk operation failed', {
    error,
    context: { userId, operation: 'riskyOperation' }
  });
  throw new CustomError('Operation failed', error);
}

// Bad
try {
  const result = await riskyOperation();
  return processResult(result);
} catch (e) {
  console.log(e);
}
```

### Error Types
- Create custom error classes for different error types
- Include error codes for easier debugging
- Always preserve the error stack

```javascript
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
    this.code = 'VALIDATION_ERROR';
  }
}
```

## Documentation

### JSDoc Comments
- Document all public functions and classes
- Include parameter types and return values
- Add examples for complex functions

```javascript
/**
 * Calculates the total price including tax
 * @param {number} price - The base price
 * @param {number} taxRate - The tax rate as a decimal (e.g., 0.08 for 8%)
 * @returns {number} The total price including tax
 * @example
 * calculateTotal(100, 0.08) // Returns 108
 */
function calculateTotal(price, taxRate) {
  return price * (1 + taxRate);
}
```

### Inline Comments
- Use comments to explain "why", not "what"
- Keep comments up-to-date with code changes
- Remove commented-out code before committing

## Testing

### Test Structure
- Use descriptive test names
- Follow AAA pattern: Arrange, Act, Assert
- Group related tests with describe blocks

```javascript
describe('UserService', () => {
  describe('createUser', () => {
    it('should create a new user with valid data', async () => {
      // Arrange
      const userData = { name: 'John', email: 'john@example.com' };
      
      // Act
      const user = await userService.createUser(userData);
      
      // Assert
      expect(user).toHaveProperty('id');
      expect(user.name).toBe(userData.name);
      expect(user.email).toBe(userData.email);
    });
    
    it('should throw error for invalid email', async () => {
      // Arrange
      const userData = { name: 'John', email: 'invalid-email' };
      
      // Act & Assert
      await expect(userService.createUser(userData))
        .rejects.toThrow(ValidationError);
    });
  });
});
```

### Test Coverage
- Aim for at least 80% code coverage
- Test edge cases and error scenarios
- Mock external dependencies
- Keep tests independent and isolated

## Additional Guidelines

### Import Organization
- Group imports by type (external, internal, types)
- Sort imports alphabetically within groups
- Use absolute imports for shared modules

```javascript
// External dependencies
import React from 'react';
import { useRouter } from 'next/router';

// Internal dependencies
import { Button } from '@/components/Button';
import { useAuth } from '@/hooks/useAuth';

// Types
import type { User } from '@/types/user';
```

### Performance Considerations
- Memoize expensive computations
- Use React.memo for pure components
- Debounce user input handlers
- Lazy load large dependencies

```javascript
// Good
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);

const debouncedSearch = useMemo(() => {
  return debounce(handleSearch, 300);
}, []);
```

---

This style guide should be treated as a living document and updated as the team's needs evolve. 