(module
  (import "synapse" "log" (func $log (param i32 i32)))
  (memory 1)
  (export "memory" (memory 0))
  (export "run" (func $run))
  
  ;; A simple string "pong" in memory
  (data (i32.const 0) "pong")

  (func $run (result i32)
    ;; Log the string "pong"
    (call $log (i32.const 0) (i32.const 4))
    
    ;; Return 1 (success)
    i32.const 1
  )
)