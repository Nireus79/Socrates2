/**
 * Socrates2 API Client for JetBrains Plugins
 *
 * Shared API client used by IntelliJ IDEA, PyCharm, and WebStorm plugins.
 * Provides unified interface for all IDE-agnostic API operations.
 */

package com.socrates2.api

import com.google.gson.*
import com.intellij.util.io.HttpRequests
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.URL
import java.net.URLEncoder
import java.util.concurrent.ConcurrentHashMap
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlinx.coroutines.*

/**
 * Main API client for Socrates2 backend
 */
class SocratesApiClient(
    private val baseUrl: String = "http://localhost:8000",
    private val authManager: AuthManager,
    private val logger: ApiLogger = DefaultApiLogger()
) {
    private val gson = Gson()
    private val requestCache = ConcurrentHashMap<String, CachedResponse>()
    private val cacheTtlMs = 5 * 60 * 1000 // 5 minutes

    // ============ Project Operations ============

    /**
     * Get all projects for current user
     */
    suspend fun getProjects(): List<Project> = withContext(Dispatchers.IO) {
        val cacheKey = "projects:all"
        val cached = getCached<List<Project>>(cacheKey)
        if (cached != null) return@withContext cached

        val url = "$baseUrl/api/v1/projects"
        val response = makeRequest("GET", url)
        val projects = gson.fromJson(
            response.getAsJsonArray("projects"),
            Array<Project>::class.java
        ).toList()

        cache(cacheKey, projects)
        projects
    }

    /**
     * Get single project by ID
     */
    suspend fun getProject(projectId: String): Project = withContext(Dispatchers.IO) {
        val cacheKey = "project:$projectId"
        val cached = getCached<Project>(cacheKey)
        if (cached != null) return@withContext cached

        val url = "$baseUrl/api/v1/projects/$projectId"
        val response = makeRequest("GET", url)
        val project = gson.fromJson(
            response.getAsJsonObject("project"),
            Project::class.java
        )

        cache(cacheKey, project)
        project
    }

    /**
     * Create new project
     */
    suspend fun createProject(name: String, description: String = ""): Project =
        withContext(Dispatchers.IO) {
            val url = "$baseUrl/api/v1/projects"
            val body = jsonObject {
                "name" to name
                "description" to description
            }

            val response = makeRequest("POST", url, body.toString())
            val project = gson.fromJson(
                response.getAsJsonObject("project"),
                Project::class.java
            )

            invalidateCache("projects:all")
            project
        }

    /**
     * Update project
     */
    suspend fun updateProject(
        projectId: String,
        name: String? = null,
        description: String? = null
    ): Project = withContext(Dispatchers.IO) {
        val url = "$baseUrl/api/v1/projects/$projectId"
        val body = jsonObject {
            if (name != null) "name" to name
            if (description != null) "description" to description
        }

        val response = makeRequest("PUT", url, body.toString())
        val project = gson.fromJson(
            response.getAsJsonObject("project"),
            Project::class.java
        )

        invalidateCache("project:$projectId")
        invalidateCache("projects:all")
        project
    }

    /**
     * Delete project
     */
    suspend fun deleteProject(projectId: String): Unit = withContext(Dispatchers.IO) {
        val url = "$baseUrl/api/v1/projects/$projectId"
        makeRequest("DELETE", url)
        invalidateCache("project:$projectId")
        invalidateCache("projects:all")
    }

    // ============ Specification Operations ============

    /**
     * Get specifications for project
     */
    suspend fun getSpecifications(projectId: String): List<Specification> =
        withContext(Dispatchers.IO) {
            val cacheKey = "specs:$projectId"
            val cached = getCached<List<Specification>>(cacheKey)
            if (cached != null) return@withContext cached

            val url = "$baseUrl/api/v1/projects/$projectId/specifications"
            val response = makeRequest("GET", url)
            val specs = gson.fromJson(
                response.getAsJsonArray("specifications"),
                Array<Specification>::class.java
            ).toList()

            cache(cacheKey, specs)
            specs
        }

    /**
     * Get single specification
     */
    suspend fun getSpecification(specId: String): Specification =
        withContext(Dispatchers.IO) {
            val cacheKey = "spec:$specId"
            val cached = getCached<Specification>(cacheKey)
            if (cached != null) return@withContext cached

            val url = "$baseUrl/api/v1/specifications/$specId"
            val response = makeRequest("GET", url)
            val spec = gson.fromJson(
                response.getAsJsonObject("specification"),
                Specification::class.java
            )

            cache(cacheKey, spec)
            spec
        }

    /**
     * Create specification
     */
    suspend fun createSpecification(
        projectId: String,
        key: String,
        value: String,
        category: String = ""
    ): Specification = withContext(Dispatchers.IO) {
        val url = "$baseUrl/api/v1/projects/$projectId/specifications"
        val body = jsonObject {
            "key" to key
            "value" to value
            "category" to category
        }

        val response = makeRequest("POST", url, body.toString())
        val spec = gson.fromJson(
            response.getAsJsonObject("specification"),
            Specification::class.java
        )

        invalidateCache("specs:$projectId")
        spec
    }

    /**
     * Update specification
     */
    suspend fun updateSpecification(
        specId: String,
        value: String? = null,
        category: String? = null
    ): Specification = withContext(Dispatchers.IO) {
        val url = "$baseUrl/api/v1/specifications/$specId"
        val body = jsonObject {
            if (value != null) "value" to value
            if (category != null) "category" to category
        }

        val response = makeRequest("PUT", url, body.toString())
        val spec = gson.fromJson(
            response.getAsJsonObject("specification"),
            Specification::class.java
        )

        invalidateCache("spec:$specId")
        spec
    }

    /**
     * Search specifications
     */
    suspend fun searchSpecifications(
        projectId: String,
        query: String,
        limit: Int = 20
    ): List<Specification> = withContext(Dispatchers.IO) {
        val params = mapOf(
            "q" to query,
            "limit" to limit.toString()
        )
        val url = "$baseUrl/api/v1/projects/$projectId/specifications/search" +
            params.toQueryString()

        val response = makeRequest("GET", url)
        gson.fromJson(
            response.getAsJsonArray("specifications"),
            Array<Specification>::class.java
        ).toList()
    }

    // ============ Conflict Operations ============

    /**
     * Get conflicts for project
     */
    suspend fun getConflicts(projectId: String): List<Conflict> =
        withContext(Dispatchers.IO) {
            val cacheKey = "conflicts:$projectId"
            val cached = getCached<List<Conflict>>(cacheKey)
            if (cached != null) return@withContext cached

            val url = "$baseUrl/api/v1/projects/$projectId/conflicts"
            val response = makeRequest("GET", url)
            val conflicts = gson.fromJson(
                response.getAsJsonArray("conflicts"),
                Array<Conflict>::class.java
            ).toList()

            cache(cacheKey, conflicts)
            conflicts
        }

    /**
     * Resolve conflict
     */
    suspend fun resolveConflict(conflictId: String, resolution: String): Conflict =
        withContext(Dispatchers.IO) {
            val url = "$baseUrl/api/v1/conflicts/$conflictId/resolve"
            val body = jsonObject {
                "resolution" to resolution
            }

            val response = makeRequest("POST", url, body.toString())
            gson.fromJson(
                response.getAsJsonObject("conflict"),
                Conflict::class.java
            )
        }

    // ============ Code Generation ============

    /**
     * Generate code from specification
     */
    suspend fun generateCode(
        specId: String,
        language: String,
        options: Map<String, String> = emptyMap()
    ): GeneratedCode = withContext(Dispatchers.IO) {
        val url = "$baseUrl/api/v1/specifications/$specId/generate"
        val body = jsonObject {
            "language" to language
            options.forEach { (k, v) -> k to v }
        }

        val response = makeRequest("POST", url, body.toString())
        GeneratedCode(
            language = language,
            code = response.get("code").asString,
            filename = response.get("filename").asString,
            formatted = response.get("formatted").asBoolean
        )
    }

    // ============ Activity Operations ============

    /**
     * Get activity feed for project
     */
    suspend fun getActivity(
        projectId: String,
        skip: Int = 0,
        limit: Int = 20
    ): List<Activity> = withContext(Dispatchers.IO) {
        val cacheKey = "activity:$projectId:$skip:$limit"
        val cached = getCached<List<Activity>>(cacheKey)
        if (cached != null) return@withContext cached

        val params = mapOf(
            "skip" to skip.toString(),
            "limit" to limit.toString()
        )
        val url = "$baseUrl/api/v1/projects/$projectId/activity" +
            params.toQueryString()

        val response = makeRequest("GET", url)
        val activities = gson.fromJson(
            response.getAsJsonArray("activities"),
            Array<Activity>::class.java
        ).toList()

        cache(cacheKey, activities)
        activities
    }

    // ============ User Operations ============

    /**
     * Get current user
     */
    suspend fun getCurrentUser(): User = withContext(Dispatchers.IO) {
        val cacheKey = "user:current"
        val cached = getCached<User>(cacheKey)
        if (cached != null) return@withContext cached

        val url = "$baseUrl/api/v1/auth/me"
        val response = makeRequest("GET", url)
        val user = gson.fromJson(
            response.getAsJsonObject("user"),
            User::class.java
        )

        cache(cacheKey, user)
        user
    }

    // ============ Health Check ============

    /**
     * Check API health
     */
    suspend fun healthCheck(): HealthStatus = withContext(Dispatchers.IO) {
        return@withContext try {
            val url = "$baseUrl/health"
            makeRequest("GET", url)
            HealthStatus(status = "healthy", latencyMs = 0)
        } catch (e: Exception) {
            logger.error("Health check failed: ${e.message}")
            HealthStatus(status = "unhealthy", latencyMs = 0, error = e.message)
        }
    }

    // ============ Private Helper Methods ============

    /**
     * Make HTTP request with automatic token handling
     */
    private suspend fun makeRequest(
        method: String,
        url: String,
        body: String? = null
    ): JsonObject = withContext(Dispatchers.IO) {
        try {
            val token = authManager.getToken()
            val headers = mutableMapOf(
                "Authorization" to "Bearer $token",
                "Content-Type" to "application/json",
                "User-Agent" to "Socrates2-JetBrains/1.0"
            )

            logger.debug("$method $url")

            val connection = URL(url).openConnection()
            headers.forEach { (k, v) -> connection.setRequestProperty(k, v) }

            if (body != null) {
                connection.setRequestProperty("Content-Length", body.length.toString())
                connection.outputStream.use { it.write(body.toByteArray()) }
            }

            val statusCode = (connection as java.net.HttpURLConnection).responseCode
            val responseBody = connection.inputStream.bufferedReader().use { it.readText() }

            if (statusCode !in 200..299) {
                val error = JsonParser.parseString(responseBody).asJsonObject
                val errorCode = error.get("error_code")?.asString ?: "UNKNOWN"
                val message = error.get("message")?.asString ?: "Request failed"
                throw ApiException(statusCode, errorCode, message)
            }

            JsonParser.parseString(responseBody).asJsonObject
        } catch (e: Exception) {
            logger.error("Request failed: ${e.message}")
            throw e
        }
    }

    /**
     * Cache response with TTL
     */
    private fun <T> cache(key: String, value: T) {
        requestCache[key] = CachedResponse(
            value = value,
            expiresAt = System.currentTimeMillis() + cacheTtlMs
        )
    }

    /**
     * Get cached response if not expired
     */
    private fun <T> getCached(key: String): T? {
        val cached = requestCache[key] ?: return null
        if (System.currentTimeMillis() > cached.expiresAt) {
            requestCache.remove(key)
            return null
        }
        return cached.value as? T
    }

    /**
     * Invalidate cache entries matching pattern
     */
    private fun invalidateCache(pattern: String) {
        requestCache.keys.removeAll { it.startsWith(pattern) }
    }

    /**
     * Extension function to convert map to query string
     */
    private fun Map<String, String>.toQueryString(): String {
        if (isEmpty()) return ""
        return "?" + entries.joinToString("&") { (k, v) ->
            "${URLEncoder.encode(k, "UTF-8")}=${URLEncoder.encode(v, "UTF-8")}"
        }
    }
}

/**
 * Helper function to create JSON objects more concisely
 */
fun jsonObject(builder: JsonObject.() -> Unit): JsonObject {
    return JsonObject().apply {
        builder()
    }
}

// Extension function to add properties
operator fun JsonObject.set(key: String, value: String) {
    addProperty(key, value)
}

// ============ Data Models ============

data class Project(
    val id: String,
    val name: String,
    val description: String,
    val ownerId: String,
    val status: String,
    val maturityScore: Int,
    val createdAt: String,
    val updatedAt: String
)

data class Specification(
    val id: String,
    val projectId: String,
    val key: String,
    val value: String,
    val category: String,
    val createdAt: String,
    val updatedAt: String
)

data class Conflict(
    val id: String,
    val projectId: String,
    val specificationId: String,
    val type: String,
    val severity: String,
    val message: String,
    val resolved: Boolean,
    val createdAt: String
)

data class Activity(
    val id: String,
    val projectId: String,
    val userId: String,
    val action: String,
    val description: String,
    val timestamp: String
)

data class User(
    val id: String,
    val email: String,
    val name: String,
    val role: String,
    val createdAt: String
)

data class GeneratedCode(
    val language: String,
    val code: String,
    val filename: String,
    val formatted: Boolean = true,
    val validated: Boolean = true,
    val lineCount: Int = 0
)

data class HealthStatus(
    val status: String,
    val latencyMs: Long,
    val error: String? = null
)

data class CachedResponse(
    val value: Any,
    val expiresAt: Long
)

// ============ API Exception ============

class ApiException(
    val statusCode: Int,
    val errorCode: String,
    message: String
) : Exception("$errorCode ($statusCode): $message")

// ============ Logging ============

interface ApiLogger {
    fun debug(message: String)
    fun info(message: String)
    fun warning(message: String)
    fun error(message: String)
}

class DefaultApiLogger : ApiLogger {
    override fun debug(message: String) = println("[DEBUG] $message")
    override fun info(message: String) = println("[INFO] $message")
    override fun warning(message: String) = println("[WARN] $message")
    override fun error(message: String) = println("[ERROR] $message")
}
