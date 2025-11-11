package com.socrates2.webstorm.extensions

import com.intellij.javascript.nodejs.PackageJsonData
import com.intellij.lang.javascript.psi.JSElement
import com.intellij.lang.javascript.psi.JSFile
import com.intellij.lang.javascript.psi.JSClass
import com.intellij.lang.javascript.psi.JSFunction
import com.intellij.openapi.project.Project
import com.intellij.psi.PsiElement
import com.socrates2.jetbrains.common.api.client.SocratesApiClient
import com.socrates2.jetbrains.common.services.CodeGeneratorService
import kotlinx.coroutines.runBlocking
import org.json.JSONObject

/**
 * WebStorm/JavaScript-specific code generation extension
 *
 * Provides JavaScript/TypeScript-specific patterns:
 * - ES6+ class syntax
 * - Arrow functions
 * - Async/await patterns
 * - Jest test generation
 * - Package.json integration
 */
class JavaScriptCodeGenerationExtension(
    private val project: Project,
    private val codeGeneratorService: CodeGeneratorService
) {
    /**
     * Generate arrow function class from specification
     */
    fun generateArrowFunctionClass(specificationId: String): String = runBlocking {
        val options = mapOf(
            "arrow_function" to "true",
            "esm" to "true",
            "async" to "true"
        )

        val result = codeGeneratorService.generateCode(
            specificationId,
            "javascript",
            options
        )

        return@runBlocking result.getOrNull()?.code ?: ""
    }

    /**
     * Generate TypeScript class with interfaces
     */
    fun generateTypeScriptClass(specificationId: String): String = runBlocking {
        val options = mapOf(
            "strict" to "true",
            "generics" to "true",
            "async" to "true"
        )

        val result = codeGeneratorService.generateCode(
            specificationId,
            "typescript",
            options
        )

        return@runBlocking result.getOrNull()?.code ?: ""
    }

    /**
     * Generate Jest test suite from specification
     */
    fun generateJestTests(specificationId: String, className: String): String {
        return """
import { $className } from './${className.replaceFirstChar { it.lowercase() }}';

describe('$className', () => {
    let instance: $className;

    beforeEach(() => {
        instance = new $className();
    });

    test('should create instance', () => {
        expect(instance).toBeDefined();
    });

    test('should validate instance', () => {
        expect(instance.validate()).toBe(true);
    });

    test('should convert to object', () => {
        const obj = instance.toObject();
        expect(obj).toBeDefined();
        expect(obj.id).toBeDefined();
    });

    test('should serialize to JSON', () => {
        const json = instance.toJSON();
        expect(json).toBeDefined();
        expect(typeof json).toBe('string');
    });

    test('should deserialize from JSON', () => {
        const json = instance.toJSON();
        const parsed = $className.fromJSON(json);
        expect(parsed.id).toBe(instance.id);
    });
});

describe('$className async operations', () => {
    let instance: $className;

    beforeEach(() => {
        instance = new $className();
    });

    test('should fetch data asynchronously', async () => {
        // Mock API client
        // const result = await instance.fetchData();
        // expect(result).toBeDefined();
    });
});
""".trimIndent()
    }

    /**
     * Generate React component from specification
     */
    fun generateReactComponent(specificationId: String, componentName: String): String {
        return """
import React, { useState, useEffect } from 'react';

interface I${componentName}Props {
    specId: string;
    onUpdate?: (data: any) => void;
}

export const $componentName: React.FC<I${componentName}Props> = ({
    specId,
    onUpdate
}) => {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                // Fetch from API
                // const result = await api.get(`/specs/${'$'}{specId}`);
                // setData(result);
                // onUpdate?.(result);
            } catch (err) {
                setError(err instanceof Error ? err : new Error('Unknown error'));
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [specId]);

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>Error: {error.message}</div>;
    }

    return (
        <div className="$componentName">
            <h2>{data?.name}</h2>
            <div className="spec-content">
                <pre>{JSON.stringify(data, null, 2)}</pre>
            </div>
        </div>
    );
};

export default $componentName;
""".trimIndent()
    }

    /**
     * Generate Vue 3 component from specification
     */
    fun generateVueComponent(specificationId: String, componentName: String): String {
        return """
<template>
    <div class="${componentName.lowercase()}">
        <h2>{{ data?.name }}</h2>
        <div v-if="loading">Loading...</div>
        <div v-if="error" class="error">{{ error.message }}</div>
        <pre v-if="data" class="spec-content">{{ JSON.stringify(data, null, 2) }}</pre>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

interface $componentName {
    id: string;
    name: string;
    value: string;
    metadata?: Record<string, any>;
}

const props = defineProps<{
    specId: string;
}>();

const emit = defineEmits<{
    update: [data: $componentName];
}>();

const data = ref<$componentName | null>(null);
const loading = ref(true);
const error = ref<Error | null>(null);

onMounted(async () => {
    try {
        // Fetch specification data
        // const result = await api.get(`/specs/${'$'}{props.specId}`);
        // data.value = result;
        // emit('update', result);
    } catch (err) {
        error.value = err instanceof Error ? err : new Error('Unknown error');
    } finally {
        loading.value = false;
    }
});
</script>

<style scoped>
.$componentName {
    padding: 1rem;
    border: 1px solid #ccc;
    border-radius: 4px;
}

.spec-content {
    background-color: #f5f5f5;
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
}

.error {
    color: #d32f2f;
    padding: 1rem;
    background-color: #ffebee;
    border-radius: 4px;
}
</style>
""".trimIndent()
    }

    /**
     * Analyze JavaScript file for specifications
     */
    fun analyzeSpecifications(file: JSFile): List<SpecificationReference> {
        val references = mutableListOf<SpecificationReference>()

        // Search for @spec, @specification comments
        val text = file.text
        val commentPattern = """@(?:spec|specification)\.(\w+(?:\.\w+)*)""".toRegex()
        val matches = commentPattern.findAll(text)

        for (match in matches) {
            references.add(
                SpecificationReference(
                    key = match.groupValues[1],
                    line = text.substringBefore(match.value).count { it == '\n' }
                )
            )
        }

        return references
    }

    /**
     * Generate ESLint configuration for project
     */
    fun generateESLintConfig(): String {
        return """
{
    "root": true,
    "parser": "@typescript-eslint/parser",
    "parserOptions": {
        "ecmaVersion": 2021,
        "sourceType": "module"
    },
    "env": {
        "browser": true,
        "node": true,
        "es2021": true
    },
    "extends": [
        "eslint:recommended",
        "plugin:@typescript-eslint/recommended"
    ],
    "rules": {
        "no-console": "warn",
        "prefer-const": "error",
        "@typescript-eslint/explicit-function-return-types": "warn"
    }
}
""".trimIndent()
    }

    /**
     * Generate package.json scripts for build/test
     */
    fun generatePackageJsonScripts(): Map<String, String> {
        return mapOf(
            "dev" to "vite",
            "build" to "tsc && vite build",
            "test" to "jest",
            "test:watch" to "jest --watch",
            "test:coverage" to "jest --coverage",
            "lint" to "eslint src --ext .ts,.tsx",
            "lint:fix" to "eslint src --ext .ts,.tsx --fix",
            "type-check" to "tsc --noEmit",
            "preview" to "vite preview",
            "generate:code" to "socrates generate --project . --language typescript"
        )
    }

    /**
     * Format JavaScript/TypeScript code
     */
    fun formatCode(code: String): String {
        val lines = code.split("\n")
        val formatted = mutableListOf<String>()
        var indentLevel = 0
        val indentStr = "  "

        for (line in lines) {
            val stripped = line.trim()

            // Decrease indent for closing braces
            if (stripped.startsWith("}") || stripped.startsWith("]") || stripped.startsWith(")")) {
                indentLevel = maxOf(0, indentLevel - 1)
            }

            if (stripped.isNotEmpty()) {
                formatted.add(indentStr.repeat(indentLevel) + stripped)
            } else {
                formatted.add("")
            }

            // Increase indent for opening braces
            if (stripped.endsWith("{") || stripped.endsWith("[") || stripped.endsWith("(")) {
                indentLevel++
            }
        }

        return formatted.joinToString("\n")
    }
}

/**
 * Specification reference found in JavaScript code
 */
data class SpecificationReference(
    val key: String,
    val line: Int
)
