# tvl

- what's a good way for the implementor to specify input/output translations, e.g., hex strings in the vectors to C arrays?
    - tvl supports a set of well-defined types, such as hex-string, b64-string, etc., and if there's a mismatch, it drops in a conversion function
- how should structure inputs/outputs be handled?
    - need a way to compare structures
    - should structures be well-defined or would we support application-specific structure types?
