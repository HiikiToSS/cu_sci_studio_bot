package main

import (
	"os"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	initdata "github.com/telegram-mini-apps/init-data-golang"
)

// Middleware which authorizes the external client.
func authMiddleware(token string) gin.HandlerFunc {
	return func(context *gin.Context) {
		// We expect passing init data in the Authorization header in the following format:
		// <auth-type> <auth-data>
		// <auth-type> must be "tma", and <auth-data> is Telegram Mini Apps init data.
		authParts := strings.Split(context.GetHeader("authorization"), " ")
		if len(authParts) != 2 {
			context.AbortWithStatusJSON(401, map[string]any{
				"message": "Unauthorized",
			})
			return
		}

		authType := authParts[0]
		authData := authParts[1]

		switch authType {
		case "tma":
			// Validate init data. We consider init data sign valid for 1 hour from their
			// creation moment.
			if err := initdata.Validate(authData, token, time.Hour); err != nil {
				context.AbortWithStatusJSON(401, map[string]any{
					"message": err.Error(),
				})
				return
			}

			// Parse init data. We will surely need it in the future.
			initData, err := initdata.Parse(authData)
			if err != nil {
				context.AbortWithStatusJSON(500, map[string]any{
					"message": err.Error(),
				})
				return
			}

			context.Request = context.Request.WithContext(
				withInitData(context.Request.Context(), initData),
			)
		}
	}
}

func main() {
	token := os.Getenv("TG_TOKEN")
	listenAddr := os.Getenv("LISTENADDR")
	if listenAddr == "" {
		listenAddr = "127.0.0.1:8080"
	}

}
