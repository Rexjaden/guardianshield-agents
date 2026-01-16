-- GuardianShield Web3 Security Plugin for APISIX
-- Advanced Web3 and blockchain-specific security checks

local core = require("apisix.core")
local json = require("apisix.core.json")
local ngx = ngx
local string = string
local pairs = pairs
local ipairs = ipairs
local tonumber = tonumber

local plugin_name = "guardianshield-web3-security"

local schema = {
    type = "object",
    properties = {
        enable_rpc_protection = {
            type = "boolean",
            default = true,
            description = "Enable JSON-RPC endpoint protection"
        },
        enable_wallet_protection = {
            type = "boolean", 
            default = true,
            description = "Enable wallet interaction protection"
        },
        enable_smart_contract_analysis = {
            type = "boolean",
            default = true,
            description = "Enable smart contract security analysis"
        },
        max_rpc_batch_size = {
            type = "integer",
            minimum = 1,
            maximum = 1000,
            default = 100,
            description = "Maximum RPC batch request size"
        },
        max_gas_limit = {
            type = "integer",
            minimum = 21000,
            maximum = 10000000,
            default = 8000000,
            description = "Maximum gas limit for transactions"
        },
        max_transaction_value = {
            type = "string",
            default = "1000000000000000000000", -- 1000 ETH in wei
            description = "Maximum transaction value in wei"
        },
        blocked_rpc_methods = {
            type = "array",
            items = {
                type = "string"
            },
            default = {
                "admin_addPeer",
                "admin_removePeer", 
                "admin_startRPC",
                "admin_stopRPC",
                "debug_setBlockProfileRate",
                "miner_start",
                "miner_stop",
                "personal_importRawKey",
                "personal_unlockAccount"
            },
            description = "RPC methods to block"
        },
        suspicious_contract_patterns = {
            type = "array", 
            items = {
                type = "string"
            },
            default = {
                "selfdestruct",
                "delegatecall",
                "suicide",
                "CREATE2",
                "STATICCALL"
            },
            description = "Suspicious smart contract patterns to detect"
        },
        rate_limit_per_address = {
            type = "integer",
            minimum = 1,
            maximum = 10000,
            default = 1000,
            description = "Rate limit per Ethereum address per hour"
        },
        enable_defi_protection = {
            type = "boolean",
            default = true,
            description = "Enable DeFi-specific protections"
        },
        enable_nft_protection = {
            type = "boolean",
            default = true,
            description = "Enable NFT-specific protections"
        }
    }
}

local _M = {
    version = 1.0,
    priority = 7900,
    name = plugin_name,
    schema = schema,
}

-- Extract Ethereum addresses from request
local function extract_ethereum_addresses(body_str)
    local addresses = {}
    if not body_str then
        return addresses
    end
    
    -- Pattern for Ethereum addresses (0x followed by 40 hex chars)
    for address in string.gmatch(body_str, "(0x[a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9])") do
        if string.len(address) == 42 then -- 0x + 40 chars
            addresses[#addresses + 1] = string.lower(address)
        end
    end
    
    return addresses
end

-- Check for suspicious RPC methods
local function check_rpc_methods(rpc_data, blocked_methods)
    local suspicious_methods = {}
    
    if rpc_data.method then
        -- Single RPC request
        for _, blocked in ipairs(blocked_methods) do
            if string.lower(rpc_data.method) == string.lower(blocked) then
                suspicious_methods[#suspicious_methods + 1] = rpc_data.method
            end
        end
    elseif type(rpc_data) == "table" then
        -- Batch RPC request
        for _, request in ipairs(rpc_data) do
            if request.method then
                for _, blocked in ipairs(blocked_methods) do
                    if string.lower(request.method) == string.lower(blocked) then
                        suspicious_methods[#suspicious_methods + 1] = request.method
                    end
                end
            end
        end
    end
    
    return suspicious_methods
end

-- Analyze transaction parameters for suspicious activity
local function analyze_transaction_params(rpc_data, conf)
    local warnings = {}
    
    local function check_transaction(tx_params)
        if not tx_params or type(tx_params) ~= "table" then
            return
        end
        
        -- Check gas limit
        if tx_params.gas then
            local gas_limit = tonumber(tx_params.gas, 16) or 0
            if gas_limit > conf.max_gas_limit then
                warnings[#warnings + 1] = "Excessive gas limit: " .. gas_limit
            end
        end
        
        -- Check transaction value
        if tx_params.value then
            local value_str = tostring(tx_params.value)
            if string.sub(value_str, 1, 2) == "0x" then
                local value_num = tonumber(value_str, 16)
                local max_value_num = tonumber(conf.max_transaction_value)
                if value_num and max_value_num and value_num > max_value_num then
                    warnings[#warnings + 1] = "Excessive transaction value: " .. value_str
                end
            end
        end
        
        -- Check for suspicious data patterns
        if tx_params.data then
            local data = string.lower(tx_params.data)
            for _, pattern in ipairs(conf.suspicious_contract_patterns) do
                if string.find(data, string.lower(pattern)) then
                    warnings[#warnings + 1] = "Suspicious contract pattern: " .. pattern
                end
            end
        end
    end
    
    if rpc_data.method and rpc_data.params then
        -- Single RPC request
        if rpc_data.method == "eth_sendTransaction" or rpc_data.method == "eth_sendRawTransaction" then
            if type(rpc_data.params) == "table" and #rpc_data.params > 0 then
                check_transaction(rpc_data.params[1])
            end
        end
    elseif type(rpc_data) == "table" then
        -- Batch RPC request
        for _, request in ipairs(rpc_data) do
            if request.method and request.params then
                if request.method == "eth_sendTransaction" or request.method == "eth_sendRawTransaction" then
                    if type(request.params) == "table" and #request.params > 0 then
                        check_transaction(request.params[1])
                    end
                end
            end
        end
    end
    
    return warnings
end

-- Check for DeFi-specific threats
local function check_defi_threats(body_str)
    if not body_str then
        return {}
    end
    
    local defi_patterns = {
        "flashloan",
        "arbitrage", 
        "sandwich",
        "frontrun",
        "mev",
        "liquidation",
        "reentrancy"
    }
    
    local threats = {}
    local lower_body = string.lower(body_str)
    
    for _, pattern in ipairs(defi_patterns) do
        if string.find(lower_body, pattern) then
            threats[#threats + 1] = pattern
        end
    end
    
    return threats
end

-- Check for NFT-specific threats
local function check_nft_threats(body_str)
    if not body_str then
        return {}
    end
    
    local nft_patterns = {
        "safeTransferFrom",
        "setApprovalForAll", 
        "approve",
        "transferFrom",
        "mint",
        "burn"
    }
    
    local threats = {}
    local lower_body = string.lower(body_str)
    
    for _, pattern in ipairs(nft_patterns) do
        if string.find(lower_body, pattern) then
            threats[#threats + 1] = pattern
        end
    end
    
    return threats
end

function _M.check_schema(conf)
    local ok, err = core.schema.check(schema, conf)
    if not ok then
        return false, err
    end
    return true
end

function _M.access(conf, ctx)
    -- Only process JSON-RPC requests
    local content_type = ctx.var.http_content_type
    if not content_type or not string.find(string.lower(content_type), "json") then
        return
    end
    
    -- Get request body
    local body_str = core.request.get_body()
    if not body_str then
        return
    end
    
    -- Parse JSON RPC request
    local rpc_data, err = json.decode(body_str)
    if not rpc_data then
        core.log.warn("Failed to parse JSON-RPC request: ", err)
        return
    end
    
    -- Check batch size limits
    if type(rpc_data) == "table" and not rpc_data.method then
        -- This is likely a batch request
        if #rpc_data > conf.max_rpc_batch_size then
            return 400, {
                error = "Batch request too large",
                code = "WEB3_BATCH_TOO_LARGE", 
                max_size = conf.max_rpc_batch_size,
                request_id = ctx.var.request_id
            }
        end
    end
    
    -- Check for blocked RPC methods
    if conf.enable_rpc_protection then
        local suspicious_methods = check_rpc_methods(rpc_data, conf.blocked_rpc_methods)
        if #suspicious_methods > 0 then
            core.log.warn("Blocked suspicious RPC methods: ", json.encode(suspicious_methods))
            return 403, {
                error = "RPC method not allowed",
                code = "WEB3_RPC_BLOCKED",
                blocked_methods = suspicious_methods,
                request_id = ctx.var.request_id
            }
        end
    end
    
    -- Analyze transaction parameters
    local tx_warnings = analyze_transaction_params(rpc_data, conf)
    if #tx_warnings > 0 then
        core.log.warn("Suspicious transaction detected: ", json.encode(tx_warnings))
        -- Don't block, but add warning headers
        core.request.set_header(ctx, "X-Web3-Warnings", json.encode(tx_warnings))
    end
    
    -- Check for DeFi threats
    if conf.enable_defi_protection then
        local defi_threats = check_defi_threats(body_str)
        if #defi_threats > 0 then
            core.log.info("DeFi activity detected: ", json.encode(defi_threats))
            core.request.set_header(ctx, "X-DeFi-Activity", json.encode(defi_threats))
        end
    end
    
    -- Check for NFT threats  
    if conf.enable_nft_protection then
        local nft_threats = check_nft_threats(body_str)
        if #nft_threats > 0 then
            core.log.info("NFT activity detected: ", json.encode(nft_threats))
            core.request.set_header(ctx, "X-NFT-Activity", json.encode(nft_threats))
        end
    end
    
    -- Extract and validate Ethereum addresses
    local eth_addresses = extract_ethereum_addresses(body_str)
    if #eth_addresses > 0 then
        core.request.set_header(ctx, "X-Ethereum-Addresses", json.encode(eth_addresses))
        
        -- Check for known malicious addresses (placeholder - would integrate with threat intel)
        local malicious_addresses = {} -- Would be populated from threat intelligence
        for _, addr in ipairs(eth_addresses) do
            for _, malicious in ipairs(malicious_addresses) do
                if addr == malicious then
                    core.log.warn("Malicious Ethereum address detected: ", addr)
                    return 403, {
                        error = "Malicious Ethereum address detected",
                        code = "WEB3_MALICIOUS_ADDRESS",
                        address = addr,
                        request_id = ctx.var.request_id
                    }
                end
            end
        end
    end
end

function _M.header_filter(conf, ctx)
    -- Add Web3-specific security headers
    local headers = {
        ["X-Web3-Protected"] = "true",
        ["X-GuardianShield-Web3"] = "active",
        ["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; connect-src 'self' wss: ws:;",
        ["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    }
    
    for name, value in pairs(headers) do
        core.response.set_header(name, value)
    end
end

function _M.log(conf, ctx)
    -- Log Web3 activity
    local web3_warnings = ctx.var.http_x_web3_warnings
    local defi_activity = ctx.var.http_x_defi_activity  
    local nft_activity = ctx.var.http_x_nft_activity
    local eth_addresses = ctx.var.http_x_ethereum_addresses
    
    if web3_warnings or defi_activity or nft_activity or eth_addresses then
        local log_data = {
            timestamp = ngx.time(),
            client_ip = core.request.get_remote_addr(ctx) or ctx.var.remote_addr,
            uri = ctx.var.uri,
            method = ctx.var.request_method,
            web3_warnings = web3_warnings and json.decode(web3_warnings) or nil,
            defi_activity = defi_activity and json.decode(defi_activity) or nil,
            nft_activity = nft_activity and json.decode(nft_activity) or nil,
            ethereum_addresses = eth_addresses and json.decode(eth_addresses) or nil,
            status = ctx.var.status,
            request_id = ctx.var.request_id,
            plugin = plugin_name
        }
        
        core.log.info("Web3 activity logged: ", json.encode(log_data))
    end
end

return _M