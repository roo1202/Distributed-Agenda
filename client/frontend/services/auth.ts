async function login(): Promise<any> {
    try {
        const resp = await $fetch('/auth/login', {
            method: 'POST',
            body: null,
          });

        return resp;

    } catch (error: any) {
        console.log(error);
        return {
            ok: false,
            data: {},
            message: error.message,
            status: "error"
        };
    }
}

export const authService = {
    login,
}