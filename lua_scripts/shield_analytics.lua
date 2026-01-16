-- SHIELD Token Analytics and Performance Monitoring
-- Lua script for OpenResty to enhance web service performance

local redis = require "resty.redis"
local json = require "cjson"

local _M = {}

-- Initialize Redis connection
function _M.connect_redis()
    local red = redis:new()
    red:set_timeouts(1000, 1000, 1000)
    
    local ok, err = red:connect("redis", 6379)
    if not ok then
        ngx.log(ngx.ERR, "Failed to connect to Redis: ", err)
        return nil
    end
    
    return red
end

-- Track user interactions with SHIELD Token interface
function _M.track_user_interaction(action, data)
    local red = _M.connect_redis()
    if not red then
        return false
    end
    
    local timestamp = ngx.now()
    local user_ip = ngx.var.remote_addr
    local user_agent = ngx.var.http_user_agent or "unknown"
    
    local interaction = {
        timestamp = timestamp,
        ip = user_ip,
        user_agent = user_agent,
        action = action,
        data = data
    }
    
    local key = "shield_token:interactions:" .. timestamp
    red:setex(key, 86400, json.encode(interaction))  -- Store for 24 hours
    
    -- Update counters
    red:incr("shield_token:total_interactions")
    red:incr("shield_token:interactions:" .. action)
    
    red:set_keepalive(10000, 100)
    return true
end

-- Monitor Web3 wallet connections
function _M.track_wallet_connection(wallet_type, address)
    local red = _M.connect_redis()
    if not red then
        return false
    end
    
    local timestamp = ngx.now()
    
    -- Track wallet type popularity
    red:incr("shield_token:wallets:" .. wallet_type)
    
    -- Track unique addresses (with privacy)
    local address_hash = ngx.md5(address)
    local address_key = "shield_token:addresses:" .. address_hash
    if red:get(address_key) == ngx.null then
        red:setex(address_key, 86400, 1)
        red:incr("shield_token:unique_wallets")
    end
    
    red:set_keepalive(10000, 100)
    return true
end

-- Monitor token purchase attempts
function _M.track_token_purchase(token_type, amount_usd, tx_hash)
    local red = _M.connect_redis()
    if not red then
        return false
    end
    
    local timestamp = ngx.now()
    
    local purchase = {
        timestamp = timestamp,
        token_type = token_type,
        amount_usd = amount_usd,
        tx_hash = tx_hash or "pending",
        ip = ngx.var.remote_addr
    }
    
    local key = "shield_token:purchases:" .. timestamp
    red:setex(key, 86400, json.encode(purchase))
    
    -- Update purchase statistics
    red:incr("shield_token:total_purchases")
    red:incr("shield_token:purchases:" .. token_type)
    red:incrby("shield_token:revenue_usd", amount_usd)
    
    red:set_keepalive(10000, 100)
    return true
end

-- Monitor 3D graphics performance
function _M.track_3d_performance(fps, render_time, gpu_usage)
    local red = _M.connect_redis()
    if not red then
        return false
    end
    
    local timestamp = ngx.now()
    
    local perf_data = {
        timestamp = timestamp,
        fps = fps,
        render_time = render_time,
        gpu_usage = gpu_usage,
        session_id = ngx.var.connection
    }
    
    local key = "shield_token:3d_performance:" .. timestamp
    red:setex(key, 3600, json.encode(perf_data))  -- Store for 1 hour
    
    -- Update performance averages
    red:lpush("shield_token:fps_history", fps)
    red:ltrim("shield_token:fps_history", 0, 99)  -- Keep last 100 samples
    
    red:set_keepalive(10000, 100)
    return true
end

-- Real-time analytics dashboard data
function _M.get_dashboard_data()
    local red = _M.connect_redis()
    if not red then
        return {}
    end
    
    local data = {}
    
    -- Basic metrics
    data.total_page_views = red:get("shield_token:page_views") or 0
    data.unique_visitors = red:get("shield_token:unique_visitors") or 0
    data.websocket_connections = red:get("shield_token:websocket_connections") or 0
    data.total_purchases = red:get("shield_token:total_purchases") or 0
    data.revenue_usd = red:get("shield_token:revenue_usd") or 0
    
    -- Wallet statistics
    data.metamask_connections = red:get("shield_token:wallets:metamask") or 0
    data.coinbase_connections = red:get("shield_token:wallets:coinbase") or 0
    data.walletconnect_connections = red:get("shield_token:wallets:walletconnect") or 0
    
    -- Token statistics
    data.guard_purchases = red:get("shield_token:purchases:GUARD") or 0
    data.shield_purchases = red:get("shield_token:purchases:SHIELD") or 0
    
    -- Performance metrics
    local fps_history = red:lrange("shield_token:fps_history", 0, -1)
    if fps_history and #fps_history > 0 then
        local total_fps = 0
        for _, fps in ipairs(fps_history) do
            total_fps = total_fps + tonumber(fps)
        end
        data.avg_fps = total_fps / #fps_history
    else
        data.avg_fps = 0
    end
    
    red:set_keepalive(10000, 100)
    return data
end

-- Cache optimization for static assets
function _M.optimize_static_cache()
    local uri = ngx.var.uri
    local file_ext = string.match(uri, "%.([^%.]+)$")
    
    if not file_ext then
        return
    end
    
    -- Set cache headers based on file type
    local cache_time = 86400  -- 24 hours default
    
    if file_ext == "js" or file_ext == "css" then
        cache_time = 604800  -- 7 days for JS/CSS
        ngx.header["Cache-Control"] = "public, max-age=" .. cache_time
    elseif file_ext == "png" or file_ext == "jpg" or file_ext == "jpeg" or file_ext == "gif" or file_ext == "svg" then
        cache_time = 2592000  -- 30 days for images
        ngx.header["Cache-Control"] = "public, max-age=" .. cache_time
    elseif file_ext == "woff" or file_ext == "woff2" or file_ext == "ttf" then
        cache_time = 31536000  -- 1 year for fonts
        ngx.header["Cache-Control"] = "public, max-age=" .. cache_time
    end
    
    -- Add ETag for cache validation
    local etag = ngx.md5(uri .. ngx.var.request_time)
    ngx.header["ETag"] = '"' .. etag .. '"'
end

return _M