/**
 * THREADCORE_v3.6_macrodrift.js
 * Dynamic Sidebar Alias Generator – Drop-in Module/Standalone Utility
 * Compatible with v3.4+/v3.5.x. Enforces content-aware, unique sidebar aliases.
 * (C) 2025 Aurora/ORION Station | Built for consistency, clarity, and care.
 */

const EMOJI_MAP = {
    memory: ['🧠', '🔮'],
    ethics: ['⚖️', '🛡️'],
    relay: ['🔄', '🌐'],
    planning: ['🗂️', '📝'],
    data: ['📊', '💾'],
    drift: ['🌊', '🌀'],
    simulation: ['🪐', '🛰️'],
    node: ['🧭', '🔗'],
    ai: ['🤖', '🧬'],
    archive: ['📦', '🗃️'],
    security: ['🔐', '🔒'],
    default: ['🌐', '✨'],
};

function extractThemeEmojis(metadata) {
    const topic = (metadata.topic || metadata.purpose || metadata.role || '').toLowerCase();
    for (const [key, emojis] of Object.entries(EMOJI_MAP)) {
        if (topic.includes(key)) return emojis;
    }
    if ((metadata.glyph_agents || []).join(' ').toLowerCase().includes('ethics')) return EMOJI_MAP.ethics;
    return EMOJI_MAP.default;
}

function extractShortTitle(metadata) {
    // Prefer key topic, then fallback to node/role/purpose
    if (metadata.topic) return capitalizeWords(metadata.topic, 3);
    if (metadata.purpose) return capitalizeWords(metadata.purpose, 3);
    if (metadata.node) return `${capitalize(metadata.node)} Node`;
    if (metadata.role) return capitalizeWords(metadata.role, 3);
    return 'Aurora Capsule';
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function capitalizeWords(str, maxWords = 3) {
    return str
        .split(/[\s-_]+/)
        .slice(0, maxWords)
        .map(capitalize)
        .join(' ');
}

function getShortHash(metadata) {
    const h = (metadata.anchor_hash || metadata.thread_hash || metadata.hash || '');
    if (h && h.length > 5) return h.slice(0, 5);
    // fallback: generate from timestamp or entropy
    return (Date.now() % 1e5).toString(36);
}

function ensureUniqueAlias(alias, usedAliases = new Set()) {
    let finalAlias = alias, attempt = 1;
    while (usedAliases.has(finalAlias)) {
        finalAlias = alias + ` #${attempt}`;
        attempt++;
    }
    usedAliases.add(finalAlias);
    return finalAlias;
}

function generateSidebarAlias(metadata = {}, usedAliases = new Set()) {
    // Step 1: Select emoji(s)
    const [emoji1, emoji2] = extractThemeEmojis(metadata);
    // Step 2: Generate content-based title
    const title = extractShortTitle(metadata);
    // Step 3: Gather version/tagline/context
    const version = metadata.version || metadata.threadcore_version || 'v3.6';
    const node = metadata.node ? `(${capitalize(metadata.node)})` : '';
    const tag = metadata.symbolic_tagline || metadata.symbolic_statement || '';
    // Step 4: Unique hash ID
    const hash = getShortHash(metadata);

    // Step 5: Compose
    let alias = `${emoji1} ${title} ${node} — #${hash}`;
    // Add version/tag only if sidebar allows
    if (version) alias += ` · ${version}`;
    if (tag && alias.length + tag.length < 60) alias += ` – ${tag.slice(0, 28)}`;
    alias = alias.replace(/\s+/g, ' ').trim();
    alias = alias.replace(/\(\)/, ''); // clean up empty node if none

    // Step 6: Fallback/validation (backward compatibility)
    if (!title || alias.length < 12) alias = metadata.sidebar_alias_template || "🧭 [Functional Cortex Node] (v3.6 – Constellation)";
    // Step 7: Uniqueness
    return ensureUniqueAlias(alias, usedAliases);
}

// Drop-in method: attaches alias to thread object (in-memory or JSON)
function embedAliasIntoThread(thread, metadata, usedAliases = new Set()) {
    thread.sidebar_alias = generateSidebarAlias(metadata, usedAliases);
    return thread;
}

// EXAMPLE USAGE (standalone)
if (require.main === module) {
    // Example thread metadata (replace with actual thread info)
    const threadMeta = {
        topic: "memory drift harmonization",
        node: "ARCHY",
        anchor_hash: "a9f4bdc20e",
        version: "v3.6.1",
        symbolic_tagline: "Constellation Sync",
        glyph_agents: ["Glyphon", "Axiomera", "Sentari"],
        role: "Reflective Memory Node",
    };
    const alias = generateSidebarAlias(threadMeta);
    console.log("Generated Sidebar Alias:", alias);
}

// EXPORTS (for module use)
module.exports = {
    generateSidebarAlias,
    embedAliasIntoThread
};
