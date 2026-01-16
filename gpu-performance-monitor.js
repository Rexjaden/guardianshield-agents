
    // GPU Performance Monitor
    const stats = {
        fps: 0,
        gpuMemory: 0,
        drawCalls: 0,
        triangles: 0
    };
    
    function updatePerformanceStats() {
        const canvas = document.querySelector('canvas');
        if (canvas && canvas.getContext) {
            const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
            if (gl) {
                const ext = gl.getExtension('WEBGL_debug_renderer_info');
                if (ext) {
                    const renderer = gl.getParameter(ext.UNMASKED_RENDERER_WEBGL);
                    console.log('GPU Renderer:', renderer);
                }
                
                // Monitor WebGL memory
                const memInfo = gl.getExtension('WEBGL_debug_renderer_info');
                if (memInfo) {
                    stats.gpuMemory = gl.getParameter(memInfo.UNMASKED_RENDERER_WEBGL);
                }
            }
        }
    }
    
    setInterval(updatePerformanceStats, 1000);
    