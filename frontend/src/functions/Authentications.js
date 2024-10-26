import { ref } from 'vue';
import apiClient from '@/api';
import { googleTokenLogin } from 'vue3-google-login';
import { createPostRequest } from './HttpRequest';
import { getCookie, setCookie, deleteCookie } from './cookies';


export var isAuth = ref(false);
export var fName = ref('');
export var lName = ref('');
export var pfp = ref('');
export var userId = ref(-1);

export async function login() {
    /**
     * Log user in with Google authentication token and set user data.
     * This function return nothing.
     */
    try {
        const logInResponse = await googleTokenLogin();
        if (isAuth.value) {
            await logout();
        }
        const response = await createPostRequest(
            `auth/google-oauth2/`,
            {
                access_token: logInResponse.access_token,
            },
        );
        setCookie('backend-token', response.data.access);
        isAuth.value = true;
        await getUserData();
    } catch (e) {
        console.error("error on login: ",e);
    }
}

export async function authStatus() {
    /**
     * Check session authentication status
     * This function does not return anything.
     */
    const token = getCookie('backend-token');
    if (token) {
        try {
            await createPostRequest(
                `rest-auth/token/verify/`,
                {
                    token: token,
                },
            );
            isAuth.value = true;
            getUserData();
        }
        catch (e) {
            await logout();
        }
    }
    else {
        await logout();
    }
}

export async function logout() {
    /**
     * Logout user from the system.
     * this function return nothing.
     */
    await createPostRequest(
        `rest-auth/logout/`,
        {},
    );
    isAuth.value = false;
    fName.value = '';
    lName.value = '';
    pfp.value = '';
    userId.value = '';
    deleteCookie('backend-token');
}

export async function getUserData() {
    /**
     * Get user data from backend.
     * this function return nothing.
     */
    try {
        const response = await apiClient.get(`rest-auth/user/`);
        fName.value = response.data.first_name;
        lName.value = response.data.last_name;
        const profilePic = await apiClient.get(`profile-pic/`);
        pfp.value = profilePic.data.profile_picture_url;
        userId.value = response.data.pk;
    } catch (e) {
        console.error(e);
        await logout();
    }
}