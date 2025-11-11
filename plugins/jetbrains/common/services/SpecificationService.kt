/**
 * Specification Service
 *
 * Handles all specification-related operations.
 */

package com.socrates2.services

import com.socrates2.api.*
import kotlinx.coroutines.*

class SpecificationService(
    private val apiClient: SocratesApiClient
) {
    /**
     * Load specifications for project
     */
    suspend fun loadSpecifications(projectId: String): Result<List<Specification>> =
        runCatching {
            apiClient.getSpecifications(projectId)
        }

    /**
     * Load specifications grouped by category
     */
    suspend fun loadSpecificationsByCategory(projectId: String):
        Result<Map<String, List<Specification>>> = runCatching {
        val specs = apiClient.getSpecifications(projectId)
        specs.groupBy { it.category }
    }

    /**
     * Get specification details
     */
    suspend fun getSpecificationDetails(specId: String): Result<SpecificationDetails> =
        runCatching {
            val spec = apiClient.getSpecification(specId)
            // In full implementation, would get more details from backend
            SpecificationDetails(
                specification = spec,
                relatedSpecifications = emptyList(),
                usageCount = 0,
                dependents = emptyList()
            )
        }

    /**
     * Create new specification
     */
    suspend fun createSpecification(
        projectId: String,
        key: String,
        value: String,
        category: String = ""
    ): Result<Specification> = runCatching {
        validateSpecification(key, value)
        apiClient.createSpecification(projectId, key, value, category)
    }

    /**
     * Update specification
     */
    suspend fun updateSpecification(
        specId: String,
        value: String? = null,
        category: String? = null
    ): Result<Specification> = runCatching {
        if (value != null) validateValue(value)
        apiClient.updateSpecification(specId, value, category)
    }

    /**
     * Search specifications
     */
    suspend fun searchSpecifications(
        projectId: String,
        query: String,
        limit: Int = 20
    ): Result<List<Specification>> = runCatching {
        if (query.isBlank()) return Result.success(emptyList())
        apiClient.searchSpecifications(projectId, query, limit)
    }

    /**
     * Get conflicts for specification
     */
    suspend fun getSpecificationConflicts(projectId: String, specId: String):
        Result<List<Conflict>> = runCatching {
        val allConflicts = apiClient.getConflicts(projectId)
        allConflicts.filter { it.specificationId == specId }
    }

    /**
     * Get specification usage
     */
    suspend fun getSpecificationUsage(projectId: String, specId: String):
        Result<SpecificationUsage> = runCatching {
        val specs = apiClient.getSpecifications(projectId)
        val spec = specs.find { it.id == specId } ?: throw IllegalArgumentException("Spec not found")

        // Count references to this spec in other specs
        val refCount = specs.count { other ->
            other.id != specId && other.value.contains(spec.key, ignoreCase = true)
        }

        SpecificationUsage(
            specificationId = specId,
            referencedBy = refCount,
            dependencies = emptyList(),
            lastModified = spec.updatedAt
        )
    }

    /**
     * Validate specification before creation/update
     */
    private fun validateSpecification(key: String, value: String) {
        validateKey(key)
        validateValue(value)
    }

    /**
     * Validate specification key
     */
    private fun validateKey(key: String) {
        if (key.isBlank()) throw IllegalArgumentException("Specification key cannot be empty")
        if (key.length > 100) throw IllegalArgumentException("Key too long (max 100 chars)")
        if (!key.matches(Regex("^[a-zA-Z0-9._-]+$"))) {
            throw IllegalArgumentException("Key contains invalid characters")
        }
    }

    /**
     * Validate specification value
     */
    private fun validateValue(value: String) {
        if (value.isBlank()) throw IllegalArgumentException("Specification value cannot be empty")
        if (value.length > 10000) throw IllegalArgumentException("Value too long (max 10000 chars)")
    }

    /**
     * Get specification statistics
     */
    suspend fun getSpecStatistics(projectId: String): Result<SpecStatistics> =
        runCatching {
            val specs = apiClient.getSpecifications(projectId)
            val categories = specs.groupingBy { it.category }.eachCount()
            val totalChars = specs.sumOf { it.value.length }

            SpecStatistics(
                projectId = projectId,
                totalCount = specs.size,
                byCategory = categories,
                totalCharacters = totalChars,
                averageLength = if (specs.isNotEmpty()) totalChars / specs.size else 0
            )
        }

    /**
     * Bulk create specifications
     */
    suspend fun bulkCreateSpecifications(
        projectId: String,
        specifications: List<CreateSpecDTO>
    ): Result<List<Specification>> = runCatching {
        coroutineScope {
            specifications.map { spec ->
                async {
                    apiClient.createSpecification(
                        projectId,
                        spec.key,
                        spec.value,
                        spec.category
                    )
                }
            }.awaitAll()
        }
    }

    /**
     * Bulk update specifications
     */
    suspend fun bulkUpdateSpecifications(
        updates: List<UpdateSpecDTO>
    ): Result<List<Specification>> = runCatching {
        coroutineScope {
            updates.map { update ->
                async {
                    apiClient.updateSpecification(
                        update.id,
                        update.value,
                        update.category
                    )
                }
            }.awaitAll()
        }
    }
}

// ============ Data Models ============

data class SpecificationDetails(
    val specification: Specification,
    val relatedSpecifications: List<Specification>,
    val usageCount: Int,
    val dependents: List<String>
)

data class SpecificationUsage(
    val specificationId: String,
    val referencedBy: Int,
    val dependencies: List<String>,
    val lastModified: String
)

data class SpecStatistics(
    val projectId: String,
    val totalCount: Int,
    val byCategory: Map<String, Int>,
    val totalCharacters: Int,
    val averageLength: Int
)

data class CreateSpecDTO(
    val key: String,
    val value: String,
    val category: String = ""
)

data class UpdateSpecDTO(
    val id: String,
    val value: String? = null,
    val category: String? = null
)
