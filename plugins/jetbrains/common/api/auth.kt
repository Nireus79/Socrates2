/**
 * Authentication Manager for JetBrains Plugins
 *
 * Handles user authentication, token management, and secure credential storage.
 */

package com.socrates2.api

import com.google.gson.JsonObject
import com.intellij.ide.passwordSafe.PasswordSafe
import com.intellij.openapi.diagnostic.Logger
import kotlinx.coroutines.*
import java.util.*

/**
 * Manages authentication and token lifecycle
 */
class AuthManager(
    private val apiUrl: String = "http://localhost:8000",
    private val logger: Logger = Logger.getInstance(AuthManager::class.java)
) {
    private val gson = com.google.gson.Gson()
    private val passwordSafe = PasswordSafe.getInstance()
    private val SERVICE_NAME = "Socrates2"
    private val TOKEN_KEY = "socrates2_access_token"
    private val REFRESH_TOKEN_KEY = "socrates2_refresh_token"
    private val USER_KEY = "socrates2_user"

    // Current session state
    private var currentToken: String? = null
    private var currentUser: User? = null
    private var tokenExpiresAt: Long = 0

    /**
     * Initialize auth manager - restore saved credentials
     */
    suspend fun initialize() = withContext(Dispatchers.IO) {
        try {
            currentToken = loadToken()
            currentUser = loadUser()

            // Verify token is still valid
            if (currentToken != null && !isTokenValid()) {
                val refreshToken = loadRefreshToken()
                if (refreshToken != null) {
                    refreshAccessToken(refreshToken)
                } else {
                    clearCredentials()
                }
            }
        } catch (e: Exception) {
            logger.warn("Failed to initialize auth: ${e.message}")
            clearCredentials()
        }
    }

    /**
     * Authenticate user with email and password
     */
    suspend fun login(email: String, password: String): AuthResponse =
        withContext(Dispatchers.IO) {
            try {
                val response = performLogin(email, password)
                saveCredentials(response)
                currentToken = response.accessToken
                currentUser = response.user
                tokenExpiresAt = calculateTokenExpiry()
                response
            } catch (e: Exception) {
                logger.error("Login failed: ${e.message}")
                throw e
            }
        }

    /**
     * Logout and clear credentials
     */
    suspend fun logout() = withContext(Dispatchers.IO) {
        try {
            currentToken?.let { token ->
                performLogout(token)
            }
        } catch (e: Exception) {
            logger.warn("Logout failed: ${e.message}")
        } finally {
            clearCredentials()
        }
    }

    /**
     * Get current access token
     */
    fun getToken(): String? {
        return currentToken ?: loadToken()
    }

    /**
     * Refresh access token using refresh token
     */
    suspend fun refreshAccessToken(refreshToken: String): String =
        withContext(Dispatchers.IO) {
            try {
                val response = performRefresh(refreshToken)
                saveToken(response.accessToken)
                saveRefreshToken(response.refreshToken)
                currentToken = response.accessToken
                tokenExpiresAt = calculateTokenExpiry()
                response.accessToken
            } catch (e: Exception) {
                logger.error("Token refresh failed: ${e.message}")
                clearCredentials()
                throw e
            }
        }

    /**
     * Check if user is authenticated
     */
    fun isAuthenticated(): Boolean {
        val token = currentToken ?: loadToken()
        return token != null && isTokenValid()
    }

    /**
     * Get current user
     */
    fun getCurrentUser(): User? {
        return currentUser ?: loadUser()
    }

    /**
     * Verify token with backend
     */
    suspend fun verifyToken(token: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val url = "$apiUrl/api/v1/auth/verify"
            val body = JsonObject().apply {
                addProperty("token", token)
            }

            val connection = java.net.URL(url).openConnection()
            connection.setRequestProperty("Authorization", "Bearer $token")
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.use { it.write(body.toString().toByteArray()) }

            val statusCode = (connection as java.net.HttpURLConnection).responseCode
            statusCode == 200
        } catch (e: Exception) {
            logger.warn("Token verification failed: ${e.message}")
            false
        }
    }

    /**
     * Validate email format
     */
    fun isValidEmail(email: String): Boolean {
        val emailRegex = "^[A-Za-z0-9+_.-]+@(.+)$".toRegex()
        return emailRegex.matches(email) && email.length <= 254
    }

    /**
     * Validate password strength
     */
    fun isValidPassword(password: String): Boolean {
        // At least 8 characters
        if (password.length < 8) return false
        // At least one uppercase
        if (!password.any { it.isUpperCase() }) return false
        // At least one lowercase
        if (!password.any { it.isLowerCase() }) return false
        // At least one digit
        if (!password.any { it.isDigit() }) return false
        return true
    }

    // ============ Private Methods ============

    /**
     * Perform login API call
     */
    private suspend fun performLogin(email: String, password: String): AuthResponse =
        withContext(Dispatchers.IO) {
            val url = "$apiUrl/api/v1/auth/login"
            val body = JsonObject().apply {
                addProperty("email", email)
                addProperty("password", password)
            }

            val connection = java.net.URL(url).openConnection()
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.use { it.write(body.toString().toByteArray()) }

            val statusCode = (connection as java.net.HttpURLConnection).responseCode
            val responseBody = connection.inputStream.bufferedReader().use { it.readText() }

            if (statusCode != 200) {
                val error = com.google.gson.JsonParser.parseString(responseBody).asJsonObject
                val message = error.get("message")?.asString ?: "Login failed"
                throw ApiException(statusCode, "LOGIN_FAILED", message)
            }

            val response = com.google.gson.JsonParser.parseString(responseBody).asJsonObject
            AuthResponse(
                accessToken = response.get("access_token").asString,
                refreshToken = response.get("refresh_token").asString,
                user = gson.fromJson(
                    response.getAsJsonObject("user"),
                    User::class.java
                ),
                expiresIn = response.get("expires_in").asInt
            )
        }

    /**
     * Perform logout API call
     */
    private suspend fun performLogout(token: String) = withContext(Dispatchers.IO) {
        try {
            val url = "$apiUrl/api/v1/auth/logout"
            val connection = java.net.URL(url).openConnection()
            connection.setRequestProperty("Authorization", "Bearer $token")
            (connection as java.net.HttpURLConnection).responseCode // Execute request
        } catch (e: Exception) {
            logger.warn("Logout API call failed: ${e.message}")
        }
    }

    /**
     * Perform token refresh API call
     */
    private suspend fun performRefresh(refreshToken: String): TokenRefreshResponse =
        withContext(Dispatchers.IO) {
            val url = "$apiUrl/api/v1/auth/refresh"
            val body = JsonObject().apply {
                addProperty("refresh_token", refreshToken)
            }

            val connection = java.net.URL(url).openConnection()
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.use { it.write(body.toString().toByteArray()) }

            val statusCode = (connection as java.net.HttpURLConnection).responseCode
            val responseBody = connection.inputStream.bufferedReader().use { it.readText() }

            if (statusCode != 200) {
                throw ApiException(statusCode, "REFRESH_FAILED", "Token refresh failed")
            }

            val response = com.google.gson.JsonParser.parseString(responseBody).asJsonObject
            TokenRefreshResponse(
                accessToken = response.get("access_token").asString,
                refreshToken = response.get("refresh_token").asString,
                expiresIn = response.get("expires_in").asInt
            )
        }

    /**
     * Save all credentials securely
     */
    private fun saveCredentials(auth: AuthResponse) {
        saveToken(auth.accessToken)
        saveRefreshToken(auth.refreshToken)
        saveUser(auth.user)
    }

    /**
     * Save access token to secure storage
     */
    private fun saveToken(token: String) {
        passwordSafe.storePassword(SERVICE_NAME, TOKEN_KEY, token)
    }

    /**
     * Load access token from secure storage
     */
    private fun loadToken(): String? {
        return passwordSafe.getPassword(SERVICE_NAME, TOKEN_KEY)
    }

    /**
     * Save refresh token to secure storage
     */
    private fun saveRefreshToken(token: String) {
        passwordSafe.storePassword(SERVICE_NAME, REFRESH_TOKEN_KEY, token)
    }

    /**
     * Load refresh token from secure storage
     */
    private fun loadRefreshToken(): String? {
        return passwordSafe.getPassword(SERVICE_NAME, REFRESH_TOKEN_KEY)
    }

    /**
     * Save user information
     */
    private fun saveUser(user: User) {
        val userJson = gson.toJson(user)
        passwordSafe.storePassword(SERVICE_NAME, USER_KEY, userJson)
    }

    /**
     * Load user information
     */
    private fun loadUser(): User? {
        return try {
            val userJson = passwordSafe.getPassword(SERVICE_NAME, USER_KEY)
            userJson?.let { gson.fromJson(it, User::class.java) }
        } catch (e: Exception) {
            logger.warn("Failed to load user: ${e.message}")
            null
        }
    }

    /**
     * Clear all credentials
     */
    private fun clearCredentials() {
        passwordSafe.storePassword(SERVICE_NAME, TOKEN_KEY, null)
        passwordSafe.storePassword(SERVICE_NAME, REFRESH_TOKEN_KEY, null)
        passwordSafe.storePassword(SERVICE_NAME, USER_KEY, null)
        currentToken = null
        currentUser = null
        tokenExpiresAt = 0
    }

    /**
     * Check if token is still valid (not expired)
     */
    private fun isTokenValid(): Boolean {
        if (currentToken == null) return false
        if (tokenExpiresAt == 0L) return true // Unknown expiry, assume valid
        return System.currentTimeMillis() < tokenExpiresAt - 60_000 // 1 minute buffer
    }

    /**
     * Calculate token expiry time from JWT
     */
    private fun calculateTokenExpiry(): Long {
        return try {
            currentToken?.let { token ->
                // Decode JWT payload (between first and second dot)
                val parts = token.split(".")
                if (parts.size < 2) return 0

                val decoded = String(
                    Base64.getUrlDecoder().decode(parts[1])
                )
                val payload = com.google.gson.JsonParser.parseString(decoded).asJsonObject
                val exp = payload.get("exp").asLong
                exp * 1000 // Convert seconds to milliseconds
            } ?: 0
        } catch (e: Exception) {
            logger.warn("Failed to extract token expiry: ${e.message}")
            0
        }
    }
}

// ============ Data Models ============

data class AuthResponse(
    val accessToken: String,
    val refreshToken: String,
    val user: User,
    val expiresIn: Int
)

data class TokenRefreshResponse(
    val accessToken: String,
    val refreshToken: String,
    val expiresIn: Int
)
