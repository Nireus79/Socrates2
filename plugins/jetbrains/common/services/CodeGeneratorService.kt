/**
 * Code Generator Service
 *
 * Provides code generation capabilities for all JetBrains plugins.
 * Coordinates with Phase 6.4 CodeGen Engine.
 */

package com.socrates2.services

import com.socrates2.api.*
import kotlinx.coroutines.*
import java.io.File

class CodeGeneratorService(
    private val apiClient: SocratesApiClient
) {
    /**
     * Generate code from specification
     */
    suspend fun generateCode(
        specificationId: String,
        language: String,
        options: Map<String, String> = emptyMap()
    ): Result<GeneratedCodeResult> = runCatching {
        validateLanguage(language)

        val generatedCode = apiClient.generateCode(
            specificationId,
            language,
            options
        )

        GeneratedCodeResult(
            code = generatedCode.code,
            language = generatedCode.language,
            filename = generatedCode.filename,
            lineCount = generatedCode.code.lines().size,
            formatted = generatedCode.formatted,
            validated = generatedCode.validated,
            generatedAt = System.currentTimeMillis()
        )
    }

    /**
     * Generate code and save to file
     */
    suspend fun generateAndSaveCode(
        specificationId: String,
        language: String,
        outputPath: String,
        options: Map<String, String> = emptyMap()
    ): Result<File> = runCatching {
        val result = generateCode(specificationId, language, options)
            .getOrThrow()

        val file = File(outputPath)
        file.parentFile?.mkdirs()
        file.writeText(result.code)

        file
    }

    /**
     * Get supported languages
     */
    fun getSupportedLanguages(): List<LanguageInfo> {
        return listOf(
            LanguageInfo("python", "Python", "py", "Python 3.8+"),
            LanguageInfo("javascript", "JavaScript", "js", "ES6+"),
            LanguageInfo("typescript", "TypeScript", "ts", "TypeScript 4.0+"),
            LanguageInfo("go", "Go", "go", "Go 1.15+"),
            LanguageInfo("java", "Java", "java", "Java 11+"),
            LanguageInfo("rust", "Rust", "rs", "Rust 2021 edition"),
            LanguageInfo("csharp", "C#", "cs", "C# 9.0+"),
            LanguageInfo("kotlin", "Kotlin", "kt", "Kotlin 1.5+")
        )
    }

    /**
     * Detect language from file extension
     */
    fun detectLanguageFromFile(filename: String): String {
        return when {
            filename.endsWith(".py") -> "python"
            filename.endsWith(".js") -> "javascript"
            filename.endsWith(".ts") -> "typescript"
            filename.endsWith(".go") -> "go"
            filename.endsWith(".java") -> "java"
            filename.endsWith(".rs") -> "rust"
            filename.endsWith(".cs") -> "csharp"
            filename.endsWith(".kt") -> "kotlin"
            else -> "auto-detect"
        }
    }

    /**
     * Get language-specific options
     */
    fun getLanguageOptions(language: String): LanguageOptions {
        return when (language.lowercase()) {
            "python" -> LanguageOptions(
                language = "python",
                supportedOptions = listOf("async", "class", "dataclass", "typing"),
                defaultOptions = mapOf("typing" to "true")
            )
            "javascript" -> LanguageOptions(
                language = "javascript",
                supportedOptions = listOf("esm", "async", "arrow_functions", "modern"),
                defaultOptions = mapOf("esm" to "true", "async" to "true")
            )
            "typescript" -> LanguageOptions(
                language = "typescript",
                supportedOptions = listOf("strict", "async", "generics", "decorators"),
                defaultOptions = mapOf("strict" to "true", "async" to "true")
            )
            "go" -> LanguageOptions(
                language = "go",
                supportedOptions = listOf("error_handling", "interfaces", "concurrency"),
                defaultOptions = mapOf("error_handling" to "explicit")
            )
            "java" -> LanguageOptions(
                language = "java",
                supportedOptions = listOf("annotations", "generics", "builder_pattern"),
                defaultOptions = mapOf("generics" to "true")
            )
            else -> LanguageOptions(language, emptyList(), emptyMap())
        }
    }

    /**
     * Format code
     */
    suspend fun formatCode(code: String, language: String): Result<String> =
        runCatching {
            validateLanguage(language)
            // Would integrate with language-specific formatters
            code
        }

    /**
     * Validate generated code
     */
    suspend fun validateCode(code: String, language: String): Result<ValidationResult> =
        runCatching {
            validateLanguage(language)

            val errors = mutableListOf<String>()
            val warnings = mutableListOf<String>()

            // Basic validation
            if (code.isBlank()) {
                errors.add("Code cannot be empty")
            }

            // Check syntax (basic)
            val syntaxValid = checkSyntax(code, language)
            if (!syntaxValid) {
                errors.add("Invalid syntax for $language")
            }

            ValidationResult(
                valid = errors.isEmpty(),
                errors = errors,
                warnings = warnings,
                language = language
            )
        }

    /**
     * Generate code with preview
     */
    suspend fun generateCodeWithPreview(
        specificationId: String,
        language: String,
        previewLines: Int = 30
    ): Result<CodePreview> = runCatching {
        val result = generateCode(specificationId, language)
            .getOrThrow()

        val lines = result.code.lines()
        val preview = lines.take(previewLines).joinToString("\n")
        val hasMore = lines.size > previewLines

        CodePreview(
            code = result.code,
            preview = preview,
            language = result.language,
            totalLines = result.lineCount,
            previewLines = previewLines,
            hasMoreCode = hasMore
        )
    }

    /**
     * Get code templates for language
     */
    fun getCodeTemplates(language: String): List<CodeTemplate> {
        return when (language.lowercase()) {
            "python" -> listOf(
                CodeTemplate("class", "Python class definition"),
                CodeTemplate("function", "Python function"),
                CodeTemplate("async", "Async function with await"),
                CodeTemplate("dataclass", "Python dataclass")
            )
            "javascript" -> listOf(
                CodeTemplate("class", "ES6 class"),
                CodeTemplate("function", "Regular function"),
                CodeTemplate("arrow", "Arrow function"),
                CodeTemplate("async", "Async function")
            )
            "typescript" -> listOf(
                CodeTemplate("interface", "TypeScript interface"),
                CodeTemplate("class", "TypeScript class"),
                CodeTemplate("type", "Type definition"),
                CodeTemplate("async", "Async function with types")
            )
            else -> emptyList()
        }
    }

    // ============ Private Methods ============

    /**
     * Validate language is supported
     */
    private fun validateLanguage(language: String) {
        val supported = getSupportedLanguages().map { it.id }
        if (language.lowercase() !in supported) {
            throw IllegalArgumentException("Unsupported language: $language")
        }
    }

    /**
     * Basic syntax checking
     */
    private fun checkSyntax(code: String, language: String): Boolean {
        return when (language.lowercase()) {
            "python" -> code.contains(Regex("""^\s*(def|class|import|if|for|while)""", RegexOption.MULTILINE))
            "javascript" -> code.contains(Regex("""(function|const|let|var|=>|async)"""))
            "typescript" -> code.contains(Regex("""(interface|type|class|async|function)"""))
            "go" -> code.contains(Regex("""(func|package|import)"""))
            "java" -> code.contains(Regex("""(class|interface|public|private)"""))
            else -> true
        }
    }
}

// ============ Data Models ============

data class GeneratedCodeResult(
    val code: String,
    val language: String,
    val filename: String,
    val lineCount: Int,
    val formatted: Boolean,
    val validated: Boolean,
    val generatedAt: Long
)

data class LanguageInfo(
    val id: String,
    val name: String,
    val extension: String,
    val version: String
)

data class LanguageOptions(
    val language: String,
    val supportedOptions: List<String>,
    val defaultOptions: Map<String, String>
)

data class ValidationResult(
    val valid: Boolean,
    val errors: List<String>,
    val warnings: List<String>,
    val language: String
)

data class CodePreview(
    val code: String,
    val preview: String,
    val language: String,
    val totalLines: Int,
    val previewLines: Int,
    val hasMoreCode: Boolean
)

data class CodeTemplate(
    val id: String,
    val description: String
)
